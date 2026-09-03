"""Endpoints de categoria."""

from flask import request
from flask_restx import Namespace, Resource

from app.controllers import parser_paginacao
from app.schemas.categoria import categoria_entrada, categoria_paginada, categoria_saida
from app.schemas.comum import erro
from app.security import usuario_atual
from app.services import categoria_service

ns = Namespace("categorias", description="Categorias de produto da empresa")

filtros = parser_paginacao()


@ns.route("")
class ListaDeCategorias(Resource):
    @ns.doc("listar_categorias", security="Bearer")
    @ns.expect(filtros)
    @ns.response(200, "Lista paginada", categoria_paginada)
    @ns.response(401, "Token ausente ou inválido", erro)
    @ns.marshal_with(categoria_paginada)
    def get(self):
        """Lista as categorias da empresa do token."""
        argumentos = filtros.parse_args()
        return categoria_service.listar(
            usuario_atual(), argumentos["pagina"], argumentos["por_pagina"]
        )

    @ns.doc("criar_categoria", security="Bearer")
    @ns.expect(categoria_entrada, validate=True)
    @ns.response(201, "Categoria criada", categoria_saida)
    @ns.response(400, "Corpo da requisição inválido", erro)
    @ns.response(422, "Nome já usado nesta empresa", erro)
    @ns.marshal_with(categoria_saida, code=201)
    def post(self):
        """Cadastra uma categoria."""
        return categoria_service.criar(usuario_atual(), request.get_json()), 201


@ns.route("/<int:categoria_id>")
@ns.param("categoria_id", "Identificador da categoria")
class CategoriaDetalhe(Resource):
    @ns.doc("obter_categoria", security="Bearer")
    @ns.response(200, "Categoria encontrada", categoria_saida)
    @ns.response(404, "Categoria não encontrada nesta empresa", erro)
    @ns.marshal_with(categoria_saida)
    def get(self, categoria_id):
        """Detalha uma categoria."""
        return categoria_service.obter(usuario_atual(), categoria_id)

    @ns.doc("atualizar_categoria", security="Bearer")
    @ns.expect(categoria_entrada, validate=True)
    @ns.response(200, "Categoria atualizada", categoria_saida)
    @ns.response(404, "Categoria não encontrada nesta empresa", erro)
    @ns.response(422, "Nome já usado nesta empresa", erro)
    @ns.marshal_with(categoria_saida)
    def put(self, categoria_id):
        """Renomeia uma categoria."""
        return categoria_service.atualizar(
            usuario_atual(), categoria_id, request.get_json()
        )

    @ns.doc("excluir_categoria", security="Bearer")
    @ns.response(204, "Categoria excluída")
    @ns.response(404, "Categoria não encontrada nesta empresa", erro)
    @ns.response(422, "Categoria em uso por algum produto", erro)
    def delete(self, categoria_id):
        """Exclui uma categoria que não esteja em uso."""
        categoria_service.remover(usuario_atual(), categoria_id)
        return "", 204
