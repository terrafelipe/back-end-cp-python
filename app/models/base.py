"""Utilitários compartilhados pelos models."""

import enum
from datetime import datetime, timezone


def clausula_in(coluna: str, enumeracao: type[enum.Enum]) -> str:
    """Monta o texto `coluna IN ('A', 'B')` a partir de uma enumeração.

    A CHECK dos enums é declarada explicitamente no `__table_args__`, em vez
    de deixar o `sa.Enum(create_constraint=True)` criá-la implicitamente: o
    autogenerate do Alembic só enxerga constraint que esteja no metadata, e
    passaria a propor a remoção dela em toda migration futura.

    Gerar o texto a partir da própria enumeração evita a lista duplicada.
    """
    valores = ", ".join(f"'{item.value}'" for item in enumeracao)
    return f"{coluna} IN ({valores})"


def agora_utc() -> datetime:
    """Instante atual em UTC, com timezone.

    Gravar sempre em UTC deixa o dado independente do fuso de quem escreveu.
    A conversão para ISO 8601 com offset acontece na serialização.
    """
    return datetime.now(timezone.utc)
