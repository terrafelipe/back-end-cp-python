"""Instâncias das extensões, criadas sem app (padrão application factory).

Ficam aqui para que models, services e resources possam importá-las sem
criar import circular com o pacote `app`.
"""

import sqlite3

from flask_jwt_extended import JWTManager
from flask_migrate import Migrate
from flask_restx import Api
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import event
from sqlalchemy.engine import Engine

db = SQLAlchemy()
migrate = Migrate()
jwt = JWTManager()

# Configuração do botão "Authorize" do Swagger, para testar rota protegida
# direto pela documentação.
authorizations = {
    "Bearer": {
        "type": "apiKey",
        "in": "header",
        "name": "Authorization",
        "description": (
            "Autenticação JWT. Faça login em POST /auth/login, copie o campo "
            "`access_token` da resposta e informe aqui no formato: "
            "**Bearer &lt;token&gt;**"
        ),
    }
}

api = Api(
    version="1.0",
    title="Gestor de Estoque API",
    description=(
        "API de gestão de estoque para pequeno comércio.\n\n"
        "O saldo de cada produto é **derivado** das movimentações — não existe "
        "coluna de saldo. Toda a regra de negócio é aplicada no backend e "
        "identificada por um código `RN-xx` na mensagem de erro."
    ),
    doc="/swagger",
    authorizations=authorizations,
    validate=True,
)


@event.listens_for(Engine, "connect")
def _ativa_foreign_keys_sqlite(dbapi_connection, connection_record):
    """Ativa a checagem de chave estrangeira no SQLite.

    O SQLite não valida FK por padrão: o PRAGMA precisa ser executado em cada
    conexão. O `isinstance` garante que isso seja inócuo se o banco for
    trocado por outro (Postgres, MySQL) via DATABASE_URL.
    """
    if isinstance(dbapi_connection, sqlite3.Connection):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()
