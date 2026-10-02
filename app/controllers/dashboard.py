"""Endpoint do dashboard: tudo o que a tela inicial usa, numa requisição."""

from flask_restx import Namespace, Resource, reqparse

from app.schemas.comum import erro
from app.schemas.dashboard import resumo_saida
from app.security import usuario_atual
from app.services import dashboard_service

ns = Namespace("dashboard", description="Números consolidados da tela inicial")

filtros = reqparse.RequestParser()
filtros.add_argument(
    "dias", type=int, default=30, location="args",
    help="Tamanho do período, de 1 a 365 dias",
)


@ns.route("/resumo")
class Resumo(Resource):
    @ns.doc("resumo_dashboard", security="Bearer")
    @ns.expect(filtros)
    @ns.response(200, "Resumo do período", resumo_saida)
    @ns.response(400, "Período fora do intervalo", erro)
    @ns.response(401, "Token ausente ou inválido", erro)
    @ns.marshal_with(resumo_saida)
    def get(self):
        """KPIs, entradas × saídas por dia, valor por categoria, top 5 saídas e alertas."""
        a = filtros.parse_args()
        return dashboard_service.resumo(usuario_atual(), a["dias"])
