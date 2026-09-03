"""Modelos de entrada e saída de fornecedor."""

from flask_restx import fields

from app.extensions import api
from app.schemas.comum import modelo_paginado

fornecedor_saida = api.model(
    "Fornecedor",
    {
        "id": fields.Integer(example=1),
        "nome": fields.String(example="Distribuidora Sul"),
        "cnpj": fields.String(example="12.345.678/0001-90"),
        "email": fields.String(example="contato@distribuidorasul.com"),
        "telefone": fields.String(example="(11) 98888-7777"),
        "empresa_id": fields.Integer(example=1),
    },
)

fornecedor_entrada = api.model(
    "FornecedorEntrada",
    {
        "nome": fields.String(required=True, min_length=2, max_length=120),
        "cnpj": fields.String(max_length=18),
        "email": fields.String(max_length=180),
        "telefone": fields.String(max_length=20),
    },
)

fornecedor_atualizacao = api.model(
    "FornecedorAtualizacao",
    {
        "nome": fields.String(min_length=2, max_length=120),
        "cnpj": fields.String(max_length=18),
        "email": fields.String(max_length=180),
        "telefone": fields.String(max_length=20),
    },
)

fornecedor_paginado = modelo_paginado("FornecedorPaginado", fornecedor_saida)
