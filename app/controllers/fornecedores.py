"""Endpoints de fornecedor. Escrita restrita a ADMIN (RN-09)."""

from flask import request
from flask_restx import Namespace, Resource

from app.controllers import parser_paginacao
from app.schemas.comum import erro
from app.schemas.fornecedor import (
    fornecedor_atualizacao,
    fornecedor_entrada,
    fornecedor_paginado,
    fornecedor_saida,
)
from app.security import somente_admin, usuario_atual
from app.services import fornecedor_service

ns = Namespace("fornecedores", description="Fornecedores da empresa (RN-09)")

filtros = parser_paginacao()


@ns.route("")
class ListaDeFornecedores(Resource):
    @ns.doc("listar_fornecedores", security="Bearer")
    @ns.expect(filtros)
    @ns.response(200, "Lista paginada", fornecedor_paginado)
    @ns.response(401, "Token ausente ou inválido", erro)
    @ns.marshal_with(fornecedor_paginado)
    def get(self):
        """Lista os fornecedores da empresa do token."""
        argumentos = filtros.parse_args()
        return fornecedor_service.listar(
            usuario_atual(), argumentos["pagina"], argumentos["por_pagina"]
        )

    @ns.doc("criar_fornecedor", security="Bearer")
    @ns.expect(fornecedor_entrada, validate=True)
    @ns.response(201, "Fornecedor criado", fornecedor_saida)
    @ns.response(403, "Exige perfil ADMIN", erro)
    @ns.response(422, "CNPJ já usado nesta empresa", erro)
    @ns.marshal_with(fornecedor_saida, code=201)
    @somente_admin
    def post(self):
        """Cadastra um fornecedor."""
        return fornecedor_service.criar(usuario_atual(), request.get_json()), 201


@ns.route("/<int:fornecedor_id>")
@ns.param("fornecedor_id", "Identificador do fornecedor")
class FornecedorDetalhe(Resource):
    @ns.doc("obter_fornecedor", security="Bearer")
    @ns.response(200, "Fornecedor encontrado", fornecedor_saida)
    @ns.response(404, "Fornecedor não encontrado nesta empresa", erro)
    @ns.marshal_with(fornecedor_saida)
    def get(self, fornecedor_id):
        """Detalha um fornecedor."""
        return fornecedor_service.obter(usuario_atual(), fornecedor_id)

    @ns.doc("atualizar_fornecedor", security="Bearer")
    @ns.expect(fornecedor_atualizacao, validate=True)
    @ns.response(200, "Fornecedor atualizado", fornecedor_saida)
    @ns.response(403, "Exige perfil ADMIN", erro)
    @ns.response(404, "Fornecedor não encontrado nesta empresa", erro)
    @ns.marshal_with(fornecedor_saida)
    @somente_admin
    def put(self, fornecedor_id):
        """Atualiza um fornecedor. Aceita alteração parcial."""
        return fornecedor_service.atualizar(
            usuario_atual(), fornecedor_id, request.get_json()
        )

    @ns.doc("excluir_fornecedor", security="Bearer")
    @ns.response(204, "Fornecedor excluído")
    @ns.response(403, "Exige perfil ADMIN", erro)
    @ns.response(422, "Fornecedor vinculado a algum produto", erro)
    @somente_admin
    def delete(self, fornecedor_id):
        """Exclui um fornecedor que não esteja vinculado a produto."""
        fornecedor_service.remover(usuario_atual(), fornecedor_id)
        return "", 204
