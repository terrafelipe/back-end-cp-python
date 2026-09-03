"""Movimentações de estoque.

O registro é imutável (RN-04): existe criação e consulta, não existe
alteração nem exclusão. Correção se faz com uma nova movimentação do tipo
AJUSTE.
"""

from datetime import datetime, timezone
from decimal import Decimal

from app.errors import NaoEncontrado, RegraDeNegocio, RequisicaoInvalida
from app.extensions import db
from app.models import Movimentacao, Produto, TipoMovimentacao
from app.services import estoque_service
from app.services.paginacao import paginar


def _da_empresa(usuario_logado):
    """Isolamento por join: movimentação não tem `empresa_id` própria (RN-08)."""
    return Movimentacao.query.join(Produto).filter(
        Produto.empresa_id == usuario_logado.empresa_id
    )


def _produto_da_empresa(usuario_logado, produto_id: int) -> Produto:
    produto = Produto.query.filter(
        Produto.id == produto_id,
        Produto.empresa_id == usuario_logado.empresa_id,
    ).first()
    if produto is None:
        raise NaoEncontrado("Produto não encontrado.")
    return produto


def _data(valor: str | None, campo: str) -> datetime | None:
    if not valor:
        return None
    try:
        lida = datetime.fromisoformat(valor)
    except ValueError:
        raise RequisicaoInvalida(
            f"O campo '{campo}' deve estar em formato ISO 8601, "
            "por exemplo 2026-09-02 ou 2026-09-02T14:30:00.",
            campo=campo,
        )
    # Compara com valor gravado em UTC; data sem fuso é tratada como UTC.
    return lida if lida.tzinfo else lida.replace(tzinfo=timezone.utc)


def listar(
    usuario_logado,
    pagina: int,
    por_pagina: int,
    produto_id: int | None = None,
    tipo: str | None = None,
    de: str | None = None,
    ate: str | None = None,
) -> dict:
    consulta = _da_empresa(usuario_logado)
    if produto_id is not None:
        consulta = consulta.filter(Movimentacao.produto_id == produto_id)
    if tipo:
        consulta = consulta.filter(Movimentacao.tipo == TipoMovimentacao(tipo))
    inicio = _data(de, "de")
    if inicio:
        consulta = consulta.filter(Movimentacao.criado_em >= inicio)
    fim = _data(ate, "ate")
    if fim:
        consulta = consulta.filter(Movimentacao.criado_em <= fim)

    return paginar(
        consulta.order_by(Movimentacao.criado_em.desc(), Movimentacao.id.desc()),
        pagina,
        por_pagina,
    )


def por_produto(usuario_logado, produto_id: int, pagina: int, por_pagina: int) -> dict:
    _produto_da_empresa(usuario_logado, produto_id)
    return listar(usuario_logado, pagina, por_pagina, produto_id=produto_id)


def registrar(usuario_logado, dados: dict) -> Movimentacao:
    """Registra a movimentação e aplica RN-02 e RN-07."""
    produto = _produto_da_empresa(usuario_logado, dados["produto_id"])
    if not produto.ativo:
        raise RegraDeNegocio(
            "HTTP-422",
            "O produto está inativo e não aceita movimentação.",
            campo="produto_id",
        )

    tipo = TipoMovimentacao(dados["tipo"])
    quantidade = dados["quantidade"]
    custo_unitario = dados.get("custo_unitario")
    saldo_atual = estoque_service.saldo(produto.id)

    if tipo is TipoMovimentacao.SAIDA and quantidade > saldo_atual:
        # RN-02 — saldo negativo representaria a venda de item inexistente.
        raise RegraDeNegocio(
            "RN-02",
            f"Saída de {quantidade} unidades excede o saldo disponível "
            f"de {saldo_atual} unidades.",
            campo="quantidade",
        )

    if tipo is TipoMovimentacao.ENTRADA:
        # RN-07 — o custo médio é recalculado antes de a entrada somar ao saldo.
        produto.preco_custo = estoque_service.custo_medio_ponderado(
            saldo_atual,
            produto.preco_custo or Decimal("0"),
            quantidade,
            custo_unitario,
        )

    movimentacao = Movimentacao(
        produto_id=produto.id,
        tipo=tipo,
        quantidade=quantidade,
        custo_unitario=custo_unitario,
        motivo=(dados.get("motivo") or "").strip() or None,
        usuario_id=usuario_logado.id,
    )
    db.session.add(movimentacao)
    db.session.commit()
    return movimentacao
