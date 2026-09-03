"""Visões consolidadas de estoque: saldo geral e alertas de ruptura."""

from flask_restx import Namespace, Resource

from app.controllers import parser_paginacao
from app.schemas.comum import erro
from app.schemas.produto import produto_paginado
from app.security import usuario_atual
from app.services import produto_service

ns = Namespace("estoque", description="Saldo consolidado e alertas de ruptura")

filtros = parser_paginacao()


@ns.route("/saldo")
class SaldoConsolidado(Resource):
    @ns.doc("saldo_consolidado", security="Bearer")
    @ns.expect(filtros)
    @ns.response(200, "Saldo de todos os produtos ativos", produto_paginado)
    @ns.response(401, "Token ausente ou inválido", erro)
    @ns.marshal_with(produto_paginado)
    def get(self):
        """Saldo atual de todos os produtos ativos da empresa."""
        a = filtros.parse_args()
        return produto_service.saldo_consolidado(
            usuario_atual(), a["pagina"], a["por_pagina"]
        )


@ns.route("/alertas")
class AlertasDeRuptura(Resource):
    @ns.doc("alertas_de_ruptura", security="Bearer")
    @ns.expect(filtros)
    @ns.response(200, "Produtos abaixo do estoque mínimo", produto_paginado)
    @ns.response(401, "Token ausente ou inválido", erro)
    @ns.marshal_with(produto_paginado)
    def get(self):
        """Produtos com saldo abaixo do estoque mínimo (RN-06)."""
        a = filtros.parse_args()
        return produto_service.em_ruptura(usuario_atual(), a["pagina"], a["por_pagina"])
