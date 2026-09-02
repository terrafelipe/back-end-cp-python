"""Modelos de entrada e saída da autenticação."""

from flask_restx import fields

from app.extensions import api
from app.schemas.usuario import usuario_saida

registro_entrada = api.model(
    "RegistroEntrada",
    {
        "empresa": fields.String(
            required=True, min_length=2, max_length=120, example="Mercado do Bairro"
        ),
        "cnpj": fields.String(
            required=True, min_length=14, max_length=18, example="12.345.678/0001-90"
        ),
        "nome": fields.String(
            required=True, min_length=2, max_length=120, example="Maria Souza"
        ),
        "email": fields.String(
            required=True, max_length=180, example="maria@mercado.com"
        ),
        "senha": fields.String(required=True, min_length=6, max_length=72),
    },
)

login_entrada = api.model(
    "LoginEntrada",
    {
        "email": fields.String(required=True, example="admin@demo.com"),
        "senha": fields.String(required=True, example="admin123"),
    },
)

token_saida = api.model(
    "Token",
    {
        "access_token": fields.String(
            description="Informe como `Bearer <token>` no cabeçalho Authorization"
        ),
        "usuario": fields.Nested(usuario_saida),
    },
)
