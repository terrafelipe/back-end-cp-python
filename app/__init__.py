"""Application factory do Gestor de Estoque."""

import logging
from pathlib import Path

from flask import Flask

from app.config import Config
from app.extensions import api, db, jwt, migrate

logger = logging.getLogger(__name__)


def create_app(config_object: type[Config] = Config) -> Flask:
    """Cria e configura a instância do Flask."""
    app = Flask(__name__)
    app.config.from_object(config_object)
    # Mesma razão do RESTX_JSON: vale para o `jsonify` do próprio Flask,
    # usado pelos tratadores de erro fora do flask-restx.
    app.json.ensure_ascii = False

    _registrar_extensoes(app)
    _registrar_tratadores_de_erro(app)
    _registrar_namespaces(app)

    return app


def aplicar_migrations(app: Flask) -> None:
    """Aplica as migrations pendentes do Alembic.

    Chamado por `run.py` e por `seed.py`, para que um clone limpo — sem banco
    e sem `.env` — funcione sem nenhum comando manual. Rodar com o banco já
    atualizado é inócuo: o Alembic detecta que está na revisão mais recente.

    Desligue com AUTO_MIGRATE=0 se quiser controlar as migrations na mão.
    """
    if not app.config.get("AUTO_MIGRATE", True):
        logger.info("AUTO_MIGRATE desligado; migrations não foram aplicadas.")
        return

    pasta_migrations = Path(app.root_path).parent / "migrations"
    if not pasta_migrations.is_dir():
        logger.warning(
            "Pasta 'migrations/' não encontrada; nada a aplicar. "
            "Gere o histórico com: flask db init && flask db migrate"
        )
        return

    from flask_migrate import upgrade

    with app.app_context():
        upgrade()


def _registrar_extensoes(app: Flask) -> None:
    db.init_app(app)
    # render_as_batch é obrigatório no SQLite: ele não tem ALTER TABLE
    # completo, e o Alembic contorna recriando a tabela. Em outros bancos o
    # modo batch é transparente, então a mesma migration serve para os dois.
    migrate.init_app(app, db, render_as_batch=True)
    jwt.init_app(app)

    # Importar os models registra as tabelas no metadata do SQLAlchemy.
    # Sem isso o autogenerate do Alembic gera uma migration vazia.
    from app import models  # noqa: F401


def _registrar_tratadores_de_erro(app: Flask) -> None:
    from app.errors import registrar_tratadores

    registrar_tratadores(app)


def _registrar_namespaces(app: Flask) -> None:
    """Registra os namespaces do flask-restx e inicializa a API.

    Os namespaces são adicionados antes do `init_app` para que apareçam
    corretamente no `/swagger`.
    """
    from app.resources.health import ns as health_ns

    api.add_namespace(health_ns, path="/health")

    api.init_app(app)
