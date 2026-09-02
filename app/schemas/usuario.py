"""Modelos de entrada e saída de usuário.

Entrada e saída são separadas de propósito: assim a senha não tem como
aparecer numa resposta, nem por engano.
"""

from flask_restx import fields

from app.extensions import api
from app.models import RoleUsuario
from app.schemas.comum import DataHoraUTC, ValorDeEnum, modelo_paginado

PAPEIS = [papel.value for papel in RoleUsuario]

usuario_saida = api.model(
    "Usuario",
    {
        "id": fields.Integer(example=1),
        "nome": fields.String(example="Maria Souza"),
        "email": fields.String(example="maria@empresa.com"),
        "role": ValorDeEnum(enum=PAPEIS, example="OPERADOR"),
        "ativo": fields.Boolean(example=True),
        "empresa_id": fields.Integer(example=1),
        "criado_em": DataHoraUTC(),
    },
)

usuario_entrada = api.model(
    "UsuarioEntrada",
    {
        "nome": fields.String(required=True, min_length=2, max_length=120),
        "email": fields.String(required=True, max_length=180),
        "senha": fields.String(required=True, min_length=6, max_length=72),
        "role": fields.String(
            required=True,
            enum=PAPEIS,
            description="ADMIN cadastra usuários e fornecedores; "
            "OPERADOR registra movimentações e consulta.",
        ),
    },
)

# Todos opcionais: o PUT aceita atualização parcial.
usuario_atualizacao = api.model(
    "UsuarioAtualizacao",
    {
        "nome": fields.String(min_length=2, max_length=120),
        "email": fields.String(max_length=180),
        "senha": fields.String(min_length=6, max_length=72),
        "role": fields.String(enum=PAPEIS),
    },
)

usuario_paginado = modelo_paginado("UsuarioPaginado", usuario_saida)
