"""Modelos de saída do relatório de reposição."""

from flask_restx import fields

from app.extensions import api
from app.models import OrigemRelatorio
from app.schemas.comum import DataHoraUTC, ValorDeEnum, modelo_paginado

prioridade = api.model("PrioridadeReposicao", {
    "sku": fields.String(example="BEB-AGUA-500"),
    "nome": fields.String(example="Água Mineral 500ml"),
    "quantidade_sugerida": fields.Integer(
        example=96, description="Calculada pelo sistema, nunca pela LLM"
    ),
    "motivo": fields.String(example="Saldo 0 abaixo do mínimo de 48."),
})

resultado = api.model("ResultadoReposicao", {
    "resumo": fields.String(example="3 produto(s) precisam de reposição; 3 já abaixo do mínimo."),
    "prioridades": fields.List(fields.Nested(prioridade)),
})

relatorio_saida = api.model("RelatorioReposicao", {
    "id": fields.Integer(example=1),
    "origem": ValorDeEnum(
        enum=[origem.value for origem in OrigemRelatorio], example="LLM",
        description="LLM = gerado por IA; REGRAS = gerado pelas regras do sistema",
    ),
    "modelo": fields.String(example="llama-3.3-70b-versatile"),
    "criado_em": DataHoraUTC(),
    "resultado": fields.Nested(resultado),
})

relatorio_paginado = modelo_paginado("RelatorioReposicaoPaginado", relatorio_saida)
