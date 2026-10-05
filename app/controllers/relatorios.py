"""Endpoints do relatório de reposição."""

from flask_restx import Namespace, Resource

from app.controllers import parser_paginacao
from app.schemas.comum import erro
from app.schemas.relatorio import relatorio_paginado, relatorio_saida
from app.security import usuario_atual
from app.services import relatorio_service

ns = Namespace(
    "relatorios", description="Relatório de reposição gerado por IA, com alternativa por regras"
)

filtros = parser_paginacao()


@ns.route("/reposicao")
class Reposicao(Resource):
    @ns.doc("gerar_relatorio_reposicao", security="Bearer")
    @ns.response(201, "Relatório gerado e salvo", relatorio_saida)
    @ns.response(401, "Token ausente ou inválido", erro)
    @ns.marshal_with(relatorio_saida, code=201)
    def post(self):
        """Gera o relatório de reposição da empresa.

        Os números são sempre do sistema; a LLM só ordena e justifica. Sem
        GROQ_API_KEY, ou se a LLM falhar ou demorar, o relatório sai pelas
        regras (origem REGRAS) — nunca erro 500.
        """
        return relatorio_service.gerar_reposicao(usuario_atual()), 201

    @ns.doc("listar_relatorios_reposicao", security="Bearer")
    @ns.expect(filtros)
    @ns.response(200, "Histórico, do mais recente ao mais antigo", relatorio_paginado)
    @ns.response(401, "Token ausente ou inválido", erro)
    @ns.marshal_with(relatorio_paginado)
    def get(self):
        """Histórico de relatórios de reposição da empresa."""
        a = filtros.parse_args()
        return relatorio_service.listar(usuario_atual(), a["pagina"], a["por_pagina"])


@ns.route("/reposicao/ultimo")
class UltimoRelatorio(Resource):
    @ns.doc("ultimo_relatorio_reposicao", security="Bearer")
    @ns.response(200, "Último relatório", relatorio_saida)
    @ns.response(404, "Nenhum relatório gerado ainda", erro)
    @ns.marshal_with(relatorio_saida)
    def get(self):
        """Último relatório gerado, sem chamar a LLM de novo."""
        return relatorio_service.ultimo(usuario_atual())
