"""Enumerações do domínio.

Herdam de `str` para que a comparação com texto funcione direto e a
serialização em JSON saia como string, sem conversão manual.
"""

import enum


class RoleUsuario(str, enum.Enum):
    """Papel do usuário dentro da empresa (RN-09, RN-10)."""

    ADMIN = "ADMIN"
    OPERADOR = "OPERADOR"


class TipoMovimentacao(str, enum.Enum):
    """Sentido da movimentação de estoque.

    O sinal da operação vem daqui, nunca do número da quantidade (RN-03).
    """

    ENTRADA = "ENTRADA"
    SAIDA = "SAIDA"
    AJUSTE = "AJUSTE"


class OrigemRelatorio(str, enum.Enum):
    """Quem escreveu o relatório de reposição: a LLM ou as regras do sistema."""

    LLM = "LLM"
    REGRAS = "REGRAS"
