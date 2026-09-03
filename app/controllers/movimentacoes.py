"""Endpoints de movimentação.

Só existe criação e consulta. Alterar ou excluir movimentação é proibido
pela RN-04, e os métodos correspondentes respondem 405 explicando a regra.
"""

from flask import request
from flask_restx import Namespace, Resource

from app.controllers import parser_paginacao
from app.errors import MetodoNaoPermitido
from app.schemas.comum import erro
from app.schemas.movimentacao import (
    movimentacao_entrada,
    movimentacao_paginada,
    movimentacao_saida,
)
from app.security import usuario_atual
from app.services import movimentacao_service

ns = Namespace("movimentacoes", description="Entradas, saídas e ajustes de estoque")

filtros = parser_paginacao()
filtros.add_argument("produto_id", type=int, location="args")
filtros.add_argument(
    "tipo", type=str, choices=("ENTRADA", "SAIDA", "AJUSTE"), location="args"
)
filtros.add_argument("de", type=str, location="args", help="Data inicial, ISO 8601")
filtros.add_argument("ate", type=str, location="args", help="Data final, ISO 8601")

MENSAGEM_RN04 = (
    "Movimentação não pode ser alterada nem excluída. "
    "Para corrigir, registre uma nova movimentação do tipo AJUSTE."
)


@ns.route("")
class ListaDeMovimentacoes(Resource):
    @ns.doc("listar_movimentacoes", security="Bearer")
    @ns.expect(filtros)
    @ns.response(200, "Extrato paginado", movimentacao_paginada)
    @ns.response(401, "Token ausente ou inválido", erro)
    @ns.marshal_with(movimentacao_paginada)
    def get(self):
        """Extrato de movimentações da empresa do token."""
        a = filtros.parse_args()
        return movimentacao_service.listar(
            usuario_atual(),
            pagina=a["pagina"],
            por_pagina=a["por_pagina"],
            produto_id=a["produto_id"],
            tipo=a["tipo"],
            de=a["de"],
            ate=a["ate"],
        )

    @ns.doc("registrar_movimentacao", security="Bearer")
    @ns.expect(movimentacao_entrada, validate=True)
    @ns.response(201, "Movimentação registrada", movimentacao_saida)
    @ns.response(400, "Corpo da requisição inválido", erro)
    @ns.response(404, "Produto não encontrado nesta empresa", erro)
    @ns.response(422, "Saída maior que o saldo disponível (RN-02)", erro)
    @ns.marshal_with(movimentacao_saida, code=201)
    def post(self):
        """Registra entrada, saída ou ajuste.

        A quantidade é sempre positiva; o sentido vem do tipo (RN-03).
        O tipo AJUSTE define o saldo pelo valor contado, em vez de somar a ele.
        """
        return movimentacao_service.registrar(usuario_atual(), request.get_json()), 201


@ns.route("/<int:movimentacao_id>")
@ns.param("movimentacao_id", "Identificador da movimentação")
class MovimentacaoDetalhe(Resource):
    @ns.doc("alterar_movimentacao", security="Bearer")
    @ns.response(405, "Movimentação é imutável (RN-04)", erro)
    def put(self, movimentacao_id):
        """Não permitido: a movimentação é imutável (RN-04)."""
        raise MetodoNaoPermitido(MENSAGEM_RN04, codigo="RN-04")

    @ns.doc("excluir_movimentacao", security="Bearer")
    @ns.response(405, "Movimentação é imutável (RN-04)", erro)
    def delete(self, movimentacao_id):
        """Não permitido: a movimentação é imutável (RN-04)."""
        raise MetodoNaoPermitido(MENSAGEM_RN04, codigo="RN-04")
