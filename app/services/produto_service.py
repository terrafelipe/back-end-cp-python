"""Produtos da própria empresa.

Saldo e ruptura vêm do cache `produto.saldo_atual` (mantido por
`movimentacao_service.registrar`), então filtro e paginação acontecem no banco.
"""

from app.errors import NaoEncontrado, RegraDeNegocio, SemPermissao
from app.extensions import db
from app.models import Categoria, Fornecedor, Produto, RoleUsuario
from app.services import estoque_service
from app.services.paginacao import paginar
from app.services.permissoes import MENSAGEM_EXCLUIR_PRODUTO, exigir_admin

CAMPOS_EDITAVEIS = (
    "sku",
    "nome",
    "descricao",
    "categoria_id",
    "fornecedor_id",
    "preco_venda",
    "estoque_minimo",
    "unidade",
)


def _da_empresa(usuario_logado):
    return Produto.query.filter(Produto.empresa_id == usuario_logado.empresa_id)


def _buscar(usuario_logado, produto_id: int) -> Produto:
    produto = _da_empresa(usuario_logado).filter(Produto.id == produto_id).first()
    if produto is None:
        raise NaoEncontrado("Produto não encontrado.")
    return produto


def _sku_em_uso(usuario_logado, sku: str, ignorar_id: int | None = None) -> bool:
    consulta = _da_empresa(usuario_logado).filter(Produto.sku == sku)
    if ignorar_id is not None:
        consulta = consulta.filter(Produto.id != ignorar_id)
    return db.session.query(consulta.exists()).scalar()


def _validar_vinculos(usuario_logado, dados: dict) -> None:
    """Categoria e fornecedor precisam existir e ser da mesma empresa (RN-08)."""
    categoria_id = dados.get("categoria_id")
    if categoria_id is not None:
        existe = Categoria.query.filter(
            Categoria.id == categoria_id,
            Categoria.empresa_id == usuario_logado.empresa_id,
        ).first()
        if existe is None:
            raise RegraDeNegocio(
                "HTTP-422", "Categoria não encontrada nesta empresa.",
                campo="categoria_id",
            )

    fornecedor_id = dados.get("fornecedor_id")
    if fornecedor_id is not None:
        existe = Fornecedor.query.filter(
            Fornecedor.id == fornecedor_id,
            Fornecedor.empresa_id == usuario_logado.empresa_id,
        ).first()
        if existe is None:
            raise RegraDeNegocio(
                "HTTP-422", "Fornecedor não encontrado nesta empresa.",
                campo="fornecedor_id",
            )


def _validar_preco_venda(usuario_logado, dados: dict, atual=None) -> None:
    """RN-09 — o preço de venda é decisão comercial, restrita ao ADMIN."""
    if "preco_venda" not in dados:
        return
    if usuario_logado.role is RoleUsuario.ADMIN:
        return
    novo = dados["preco_venda"]
    # Deixa o OPERADOR criar produto sem mexer em preço, e editar produto
    # desde que não altere o valor.
    if atual is not None and str(atual) == str(novo):
        return
    if atual is None and not novo:
        return
    raise SemPermissao(
        "Apenas ADMIN pode definir o preço de venda.", codigo="RN-09"
    )


def _com_saldo(produtos: list[Produto]) -> list[Produto]:
    """Expõe o cache como `saldo` e calcula `em_ruptura`, para o marshal encontrar."""
    for produto in produtos:
        produto.saldo = produto.saldo_atual
        produto.em_ruptura = estoque_service.em_ruptura(
            produto.estoque_minimo, produto.saldo_atual
        )
    return produtos


def listar(
    usuario_logado,
    pagina: int,
    por_pagina: int,
    busca: str | None = None,
    categoria_id: int | None = None,
    em_ruptura: bool | None = None,
    incluir_inativos: bool = False,
) -> dict:
    consulta = _da_empresa(usuario_logado)
    if not incluir_inativos:
        consulta = consulta.filter(Produto.ativo.is_(True))
    if categoria_id is not None:
        consulta = consulta.filter(Produto.categoria_id == categoria_id)
    if busca:
        termo = f"%{busca.strip()}%"
        consulta = consulta.filter(
            db.or_(Produto.nome.ilike(termo), Produto.sku.ilike(termo))
        )
    if em_ruptura is True:
        consulta = consulta.filter(estoque_service.condicao_ruptura())
    elif em_ruptura is False:
        consulta = consulta.filter(~estoque_service.condicao_ruptura())

    pagina_atual = paginar(consulta.order_by(Produto.nome), pagina, por_pagina)
    _com_saldo(pagina_atual["itens"])
    return pagina_atual


def obter(usuario_logado, produto_id: int) -> Produto:
    return _com_saldo([_buscar(usuario_logado, produto_id)])[0]


def criar(usuario_logado, dados: dict) -> Produto:
    _validar_preco_venda(usuario_logado, dados)
    _validar_vinculos(usuario_logado, dados)

    sku = dados["sku"].strip()
    if _sku_em_uso(usuario_logado, sku):
        raise RegraDeNegocio(
            "RN-01", "Já existe um produto com este SKU nesta empresa.", campo="sku"
        )

    produto = Produto(sku=sku, empresa_id=usuario_logado.empresa_id)
    for campo in CAMPOS_EDITAVEIS:
        if campo in dados and campo != "sku":
            setattr(produto, campo, dados[campo])
    db.session.add(produto)
    db.session.commit()
    return _com_saldo([produto])[0]


def atualizar(usuario_logado, produto_id: int, dados: dict) -> Produto:
    produto = _buscar(usuario_logado, produto_id)
    _validar_preco_venda(usuario_logado, dados, atual=produto.preco_venda)
    _validar_vinculos(usuario_logado, dados)

    if "sku" in dados:
        sku = dados["sku"].strip()
        if _sku_em_uso(usuario_logado, sku, ignorar_id=produto.id):
            raise RegraDeNegocio(
                "RN-01", "Já existe um produto com este SKU nesta empresa.", campo="sku"
            )
        produto.sku = sku

    for campo in CAMPOS_EDITAVEIS:
        if campo in dados and campo != "sku":
            setattr(produto, campo, dados[campo])
    db.session.commit()
    return _com_saldo([produto])[0]


def desativar(usuario_logado, produto_id: int) -> None:
    """RN-05 e RN-10 — inativa o produto; excluir quebraria o histórico."""
    exigir_admin(
        usuario_logado, codigo="RN-10", mensagem=MENSAGEM_EXCLUIR_PRODUTO
    )
    produto = _buscar(usuario_logado, produto_id)
    produto.ativo = False
    db.session.commit()


def em_ruptura(usuario_logado, pagina: int, por_pagina: int) -> dict:
    """RN-06 — produtos ativos com saldo abaixo do mínimo."""
    return listar(
        usuario_logado, pagina, por_pagina, em_ruptura=True
    )


def saldo_consolidado(usuario_logado, pagina: int, por_pagina: int) -> dict:
    """Saldo de todos os produtos ativos da empresa."""
    return listar(usuario_logado, pagina, por_pagina)
