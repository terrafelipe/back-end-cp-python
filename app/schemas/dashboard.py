"""Modelo de saída do dashboard: uma tela, um endpoint."""

from flask_restx import fields

from app.extensions import api
from app.schemas.produto import produto_saida

periodo = api.model("PeriodoDashboard", {
    "de": fields.Date(example="2026-08-27"),
    "ate": fields.Date(example="2026-09-25"),
    "dias": fields.Integer(example=30),
})

kpis = api.model("KpisDashboard", {
    "valor_estoque": fields.Float(
        example=4821.37, description="Soma de saldo × custo médio dos produtos ativos"
    ),
    "produtos_ativos": fields.Integer(example=8),
    "em_ruptura": fields.Integer(example=3, description="Ativos abaixo do mínimo (RN-06)"),
    "movimentacoes": fields.Integer(example=412, description="Registradas no período"),
})

ponto_serie = api.model("PontoSerieDiaria", {
    "data": fields.String(example="2026-09-25"),
    "entradas": fields.Integer(example=120),
    "saidas": fields.Integer(example=64),
})

valor_categoria = api.model("ValorPorCategoria", {
    "categoria": fields.String(example="Bebidas"),
    "valor": fields.Float(example=1520.4),
})

top_saida = api.model("TopSaida", {
    "produto_id": fields.Integer(example=2),
    "nome": fields.String(example="Água Mineral 500ml"),
    "quantidade": fields.Integer(example=610),
})

resumo_saida = api.model("ResumoDashboard", {
    "periodo": fields.Nested(periodo),
    "kpis": fields.Nested(kpis),
    "serie_diaria": fields.List(fields.Nested(ponto_serie)),
    "valor_por_categoria": fields.List(fields.Nested(valor_categoria)),
    "top_saidas": fields.List(fields.Nested(top_saida)),
    "alertas": fields.List(fields.Nested(produto_saida)),
})
