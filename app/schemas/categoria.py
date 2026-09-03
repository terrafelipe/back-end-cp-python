"""Modelos de entrada e saída de categoria."""

from flask_restx import fields

from app.extensions import api
from app.schemas.comum import modelo_paginado

categoria_saida = api.model(
    "Categoria",
    {
        "id": fields.Integer(example=1),
        "nome": fields.String(example="Bebidas"),
        "empresa_id": fields.Integer(example=1),
    },
)

categoria_entrada = api.model(
    "CategoriaEntrada",
    {"nome": fields.String(required=True, min_length=2, max_length=80, example="Congelados")},
)

categoria_paginada = modelo_paginado("CategoriaPaginada", categoria_saida)
