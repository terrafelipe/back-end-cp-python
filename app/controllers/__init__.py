"""Camada HTTP.

Os controllers apenas recebem a requisição, chamam o serviço e devolvem a
resposta. Nenhuma regra de negócio é decidida aqui.
"""

from flask_restx import inputs, reqparse

from app.services.paginacao import POR_PAGINA_PADRAO


def parser_paginacao() -> reqparse.RequestParser:
    """Parser com os dois parâmetros comuns a toda listagem."""
    parser = reqparse.RequestParser()
    parser.add_argument("pagina", type=int, default=1, location="args")
    parser.add_argument(
        "por_pagina", type=int, default=POR_PAGINA_PADRAO, location="args"
    )
    return parser


def argumento_booleano(parser, nome: str, ajuda: str, padrao=False) -> None:
    """Adiciona um booleano de query string.

    `type=bool` não serve: `bool("false")` é verdadeiro, então `?x=false`
    ligaria o filtro. `inputs.boolean` interpreta o texto corretamente.
    """
    parser.add_argument(
        nome, type=inputs.boolean, default=padrao, location="args", help=ajuda
    )
