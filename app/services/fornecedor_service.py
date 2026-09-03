"""Fornecedores da própria empresa.

Criar, alterar e excluir exigem ADMIN (RN-09); consultar não.
"""

from app.errors import NaoEncontrado, RegraDeNegocio
from app.extensions import db
from app.models import Fornecedor, Produto
from app.services.paginacao import paginar
from app.services.permissoes import exigir_admin

CAMPOS_EDITAVEIS = ("nome", "cnpj", "email", "telefone")


def _da_empresa(usuario_logado):
    return Fornecedor.query.filter(Fornecedor.empresa_id == usuario_logado.empresa_id)


def _buscar(usuario_logado, fornecedor_id: int) -> Fornecedor:
    fornecedor = (
        _da_empresa(usuario_logado).filter(Fornecedor.id == fornecedor_id).first()
    )
    if fornecedor is None:
        raise NaoEncontrado("Fornecedor não encontrado.")
    return fornecedor


def _cnpj_em_uso(usuario_logado, cnpj: str, ignorar_id: int | None = None) -> bool:
    consulta = _da_empresa(usuario_logado).filter(Fornecedor.cnpj == cnpj)
    if ignorar_id is not None:
        consulta = consulta.filter(Fornecedor.id != ignorar_id)
    return db.session.query(consulta.exists()).scalar()


def _aplicar(usuario_logado, fornecedor: Fornecedor, dados: dict) -> None:
    for campo in CAMPOS_EDITAVEIS:
        if campo not in dados:
            continue
        valor = dados[campo]
        valor = valor.strip() if isinstance(valor, str) else valor
        if campo == "cnpj" and valor and _cnpj_em_uso(
            usuario_logado, valor, ignorar_id=fornecedor.id
        ):
            raise RegraDeNegocio(
                "HTTP-422", "Já existe um fornecedor com este CNPJ.", campo="cnpj"
            )
        setattr(fornecedor, campo, valor or None)


def listar(usuario_logado, pagina: int, por_pagina: int) -> dict:
    return paginar(
        _da_empresa(usuario_logado).order_by(Fornecedor.nome), pagina, por_pagina
    )


def obter(usuario_logado, fornecedor_id: int) -> Fornecedor:
    return _buscar(usuario_logado, fornecedor_id)


def criar(usuario_logado, dados: dict) -> Fornecedor:
    exigir_admin(usuario_logado)
    fornecedor = Fornecedor(
        nome=dados["nome"].strip(), empresa_id=usuario_logado.empresa_id
    )
    _aplicar(usuario_logado, fornecedor, dados)
    db.session.add(fornecedor)
    db.session.commit()
    return fornecedor


def atualizar(usuario_logado, fornecedor_id: int, dados: dict) -> Fornecedor:
    exigir_admin(usuario_logado)
    fornecedor = _buscar(usuario_logado, fornecedor_id)
    _aplicar(usuario_logado, fornecedor, dados)
    db.session.commit()
    return fornecedor


def remover(usuario_logado, fornecedor_id: int) -> None:
    exigir_admin(usuario_logado)
    fornecedor = _buscar(usuario_logado, fornecedor_id)
    em_uso = Produto.query.filter(Produto.fornecedor_id == fornecedor.id).count()
    if em_uso:
        raise RegraDeNegocio(
            "HTTP-422",
            f"O fornecedor está vinculado a {em_uso} produto(s) e não pode ser excluído.",
        )
    db.session.delete(fornecedor)
    db.session.commit()
