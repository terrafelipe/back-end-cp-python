"""Endpoints de produto."""

from flask import request
from flask_restx import Namespace, Resource, inputs

from app.controllers import argumento_booleano, parser_paginacao
from app.schemas.comum import erro
from app.schemas.movimentacao import movimentacao_paginada
from app.schemas.produto import (
    produto_atualizacao,
    produto_entrada,
    produto_paginado,
    produto_saida,
)
from app.security import somente_admin, usuario_atual
from app.services import movimentacao_service, produto_service
from app.services.permissoes import MENSAGEM_EXCLUIR_PRODUTO

ns = Namespace("produtos", description="Produtos da empresa, com saldo derivado")

filtros = parser_paginacao()
filtros.add_argument(
    "busca", type=str, location="args", help="Trecho do nome ou do SKU"
)
filtros.add_argument("categoria_id", type=int, location="args")
filtros.add_argument(
    "em_ruptura",
    type=inputs.boolean,
    location="args",
    help="Quando verdadeiro, lista só os produtos abaixo do estoque mínimo (RN-06)",
)
argumento_booleano(
    filtros, "incluir_inativos", "Inclui na listagem os produtos já inativados"
)

filtros_historico = parser_paginacao()


@ns.route("")
class ListaDeProdutos(Resource):
    @ns.doc("listar_produtos", security="Bearer")
    @ns.expect(filtros)
    @ns.response(200, "Lista paginada, cada item com saldo apurado", produto_paginado)
    @ns.response(401, "Token ausente ou inválido", erro)
    @ns.marshal_with(produto_paginado)
    def get(self):
        """Lista os produtos da empresa do token.

        Cada item traz o saldo apurado das movimentações e o indicador de
        ruptura — nenhum dos dois é coluna do banco.
        """
        a = filtros.parse_args()
        return produto_service.listar(
            usuario_atual(),
            pagina=a["pagina"],
            por_pagina=a["por_pagina"],
            busca=a["busca"],
            categoria_id=a["categoria_id"],
            em_ruptura=a["em_ruptura"],
            incluir_inativos=a["incluir_inativos"],
        )

    @ns.doc("criar_produto", security="Bearer")
    @ns.expect(produto_entrada, validate=True)
    @ns.response(201, "Produto criado", produto_saida)
    @ns.response(400, "Corpo da requisição inválido", erro)
    @ns.response(403, "OPERADOR não define preço de venda (RN-09)", erro)
    @ns.response(422, "SKU já usado, ou categoria/fornecedor inexistente", erro)
    @ns.marshal_with(produto_saida, code=201)
    def post(self):
        """Cadastra um produto."""
        return produto_service.criar(usuario_atual(), request.get_json()), 201


@ns.route("/<int:produto_id>")
@ns.param("produto_id", "Identificador do produto")
class ProdutoDetalhe(Resource):
    @ns.doc("obter_produto", security="Bearer")
    @ns.response(200, "Produto encontrado, com saldo atual", produto_saida)
    @ns.response(404, "Produto não encontrado nesta empresa", erro)
    @ns.marshal_with(produto_saida)
    def get(self, produto_id):
        """Detalha o produto, incluindo o saldo atual."""
        return produto_service.obter(usuario_atual(), produto_id)

    @ns.doc("atualizar_produto", security="Bearer")
    @ns.expect(produto_atualizacao, validate=True)
    @ns.response(200, "Produto atualizado", produto_saida)
    @ns.response(403, "OPERADOR não altera preço de venda (RN-09)", erro)
    @ns.response(404, "Produto não encontrado nesta empresa", erro)
    @ns.response(422, "SKU já usado, ou categoria/fornecedor inexistente", erro)
    @ns.marshal_with(produto_saida)
    def put(self, produto_id):
        """Atualiza um produto. Aceita alteração parcial."""
        return produto_service.atualizar(
            usuario_atual(), produto_id, request.get_json()
        )

    @ns.doc("inativar_produto", security="Bearer")
    @ns.response(204, "Produto inativado")
    @ns.response(403, "OPERADOR não exclui produto (RN-10)", erro)
    @ns.response(404, "Produto não encontrado nesta empresa", erro)
    @somente_admin(codigo="RN-10", mensagem=MENSAGEM_EXCLUIR_PRODUTO)
    def delete(self, produto_id):
        """Inativa o produto.

        Não apaga: o histórico de movimentação referencia o item, e excluir
        deixaria o extrato sem sentido (RN-05).
        """
        produto_service.desativar(usuario_atual(), produto_id)
        return "", 204


@ns.route("/<int:produto_id>/movimentacoes")
@ns.param("produto_id", "Identificador do produto")
class HistoricoDoProduto(Resource):
    @ns.doc("historico_do_produto", security="Bearer")
    @ns.expect(filtros_historico)
    @ns.response(200, "Extrato do produto", movimentacao_paginada)
    @ns.response(404, "Produto não encontrado nesta empresa", erro)
    @ns.marshal_with(movimentacao_paginada)
    def get(self, produto_id):
        """Histórico do produto, da movimentação mais recente para a mais antiga."""
        a = filtros_historico.parse_args()
        return movimentacao_service.por_produto(
            usuario_atual(), produto_id, a["pagina"], a["por_pagina"]
        )
