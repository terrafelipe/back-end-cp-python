"""Configuração da aplicação, lida de variáveis de ambiente.

Todos os valores têm default de desenvolvimento para que o projeto rode logo
após o clone, sem `.env`. Em qualquer ambiente que não seja o local, as chaves
devem obrigatoriamente vir do ambiente.
"""

import os
from datetime import timedelta
from pathlib import Path

from dotenv import load_dotenv

# Raiz do projeto (pasta que contém `app/`, `run.py`, `estoque.db`).
BASE_DIR = Path(__file__).resolve().parent.parent

# Carrega o `.env` da raiz, se existir. Variáveis já presentes no ambiente
# têm precedência sobre o arquivo.
load_dotenv(BASE_DIR / ".env")


def _env_bool(name: str, default: bool = False) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def _env_int(name: str, default: int) -> int:
    raw = os.getenv(name)
    if raw is None or not raw.strip():
        return default
    return int(raw)


class Config:
    """Configuração única, parametrizada por ambiente."""

    # --- Flask ---------------------------------------------------------
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-nao-usar-em-producao")
    DEBUG = _env_bool("FLASK_DEBUG", default=True)

    # --- Banco de dados ------------------------------------------------
    # Default: SQLite em arquivo na raiz do projeto. Trocar de banco é só
    # mudar DATABASE_URL — nenhum tipo de coluna específico é usado.
    SQLALCHEMY_DATABASE_URI = (
        os.getenv("DATABASE_URL") or f"sqlite:///{(BASE_DIR / 'estoque.db').as_posix()}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ECHO = _env_bool("SQLALCHEMY_ECHO", default=False)

    # --- JWT -----------------------------------------------------------
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY") or SECRET_KEY
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=_env_int("JWT_EXPIRES_HOURS", 8))

    # --- API / Swagger -------------------------------------------------
    API_TITLE = "Gestor de Estoque API"
    API_VERSION = "1.0"
    SWAGGER_URL = os.getenv("SWAGGER_URL", "/swagger")
    # Esconde o header X-Fields do Swagger; deixa a documentação mais limpa.
    RESTX_MASK_SWAGGER = False

    # --- Servidor local ------------------------------------------------
    HOST = os.getenv("HOST", "127.0.0.1")
    PORT = _env_int("PORT", 5000)
