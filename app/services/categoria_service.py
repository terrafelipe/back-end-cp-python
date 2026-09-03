"""Categorias da própria empresa.

Sem restrição de papel: classificar produto é tarefa de operação.
"""

from app.errors import NaoEncontrado, RegraDeNegocio
from app.extensions import db
from app.models import Categoria, Produto
from app.services.paginacao import paginar


def _da_empresa(usuario_logado):
    return Categoria.query.filter(Categoria.empresa_id == usuario_logado.empresa_id)


def _buscar(usuario_logado, categoria_id: int) -> Categoria:
    categoria = _da_empresa(usuario_logado).filter(Categoria.id == categoria_id).first()
    if categoria is None:
        raise NaoEncontrado("Categoria não encontrada.")
    return categoria


def _nome_em_uso(usuario_logado, nome: str, ignorar_id: int | None = None) -> bool:
    consulta = _da_empresa(usuario_logado).filter(Categoria.nome == nome)
    if ignorar_id is not None:
        consulta = consulta.filter(Categoria.id != ignorar_id)
    return db.session.query(consulta.exists()).scalar()


def listar(usuario_logado, pagina: int, por_pagina: int) -> dict:
    return paginar(
        _da_empresa(usuario_logado).order_by(Categoria.nome), pagina, por_pagina
    )


def obter(usuario_logado, categoria_id: int) -> Categoria:
    return _buscar(usuario_logado, categoria_id)


def criar(usuario_logado, dados: dict) -> Categoria:
    nome = dados["nome"].strip()
    if _nome_em_uso(usuario_logado, nome):
        raise RegraDeNegocio(
            "HTTP-422", "Já existe uma categoria com este nome.", campo="nome"
        )
    categoria = Categoria(nome=nome, empresa_id=usuario_logado.empresa_id)
    db.session.add(categoria)
    db.session.commit()
    return categoria


def atualizar(usuario_logado, categoria_id: int, dados: dict) -> Categoria:
    categoria = _buscar(usuario_logado, categoria_id)
    nome = dados["nome"].strip()
    if _nome_em_uso(usuario_logado, nome, ignorar_id=categoria.id):
        raise RegraDeNegocio(
            "HTTP-422", "Já existe uma categoria com este nome.", campo="nome"
        )
    categoria.nome = nome
    db.session.commit()
    return categoria


def remover(usuario_logado, categoria_id: int) -> None:
    categoria = _buscar(usuario_logado, categoria_id)
    # `produto.categoria_id` é obrigatório: apagar deixaria produto órfão.
    em_uso = Produto.query.filter(Produto.categoria_id == categoria.id).count()
    if em_uso:
        raise RegraDeNegocio(
            "HTTP-422",
            f"A categoria está em uso por {em_uso} produto(s) e não pode ser excluída.",
        )
    db.session.delete(categoria)
    db.session.commit()
