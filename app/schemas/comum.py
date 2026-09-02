"""Campos e modelos compartilhados por todos os recursos."""

from datetime import timezone
from enum import Enum

from flask_restx import fields

from app.extensions import api


class DataHoraUTC(fields.Raw):
    """Serializa data e hora em ISO 8601 com offset.

    O SQLite não guarda o fuso: o valor gravado com timezone volta ingênuo.
    Como tudo é gravado em UTC, o fuso é reaplicado aqui, na leitura. Em
    bancos que preservam o offset o valor já chega consciente e passa direto,
    então o mesmo código serve para os dois.
    """

    __schema_type__ = "string"
    __schema_format__ = "date-time"
    __schema_example__ = "2026-09-02T14:30:00+00:00"

    def format(self, valor):
        if valor is None:
            return None
        if valor.tzinfo is None:
            valor = valor.replace(tzinfo=timezone.utc)
        return valor.isoformat()


class ValorDeEnum(fields.String):
    """Serializa uma enumeração pelo seu valor.

    `fields.String` chamaria `str()` no membro, que devolve
    "RoleUsuario.ADMIN" em vez de "ADMIN".
    """

    def format(self, valor):
        return valor.value if isinstance(valor, Enum) else str(valor)


detalhe_erro = api.model(
    "DetalheErro",
    {
        "codigo": fields.String(
            description="Identificador da regra violada", example="RN-02"
        ),
        "mensagem": fields.String(
            description="Explicação legível do que impediu a operação",
            example="Saída de 50 unidades excede o saldo disponível de 12 unidades.",
        ),
        "campo": fields.String(
            description="Campo do corpo que causou o erro, quando aplicável",
            example="quantidade",
        ),
    },
)

erro = api.model("Erro", {"erro": fields.Nested(detalhe_erro)})


def modelo_paginado(nome: str, modelo_item):
    """Monta o envelope de listagem para um tipo de item.

    O formato é idêntico em todos os recursos paginados; só muda o conteúdo
    de `itens`.
    """
    return api.model(
        nome,
        {
            "itens": fields.List(fields.Nested(modelo_item)),
            "pagina": fields.Integer(example=1),
            "por_pagina": fields.Integer(example=20),
            "total": fields.Integer(example=137),
            "total_paginas": fields.Integer(example=7),
        },
    )
