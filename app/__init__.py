"""Application factory do Gestor de Estoque."""

from flask import Flask

from app.config import Config
from app.extensions import api, db, jwt, migrate


def create_app(config_object: type[Config] = Config) -> Flask:
    """Cria e configura a instância do Flask."""
    app = Flask(__name__)
    app.config.from_object(config_object)

    _registrar_extensoes(app)
    _registrar_namespaces(app)

    return app


def _registrar_extensoes(app: Flask) -> None:
    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)


def _registrar_namespaces(app: Flask) -> None:
    """Registra os namespaces do flask-restx e inicializa a API.

    Os namespaces são adicionados antes do `init_app` para que apareçam
    corretamente no `/swagger`.
    """
    from app.resources.health import ns as health_ns

    api.add_namespace(health_ns, path="/health")

    api.init_app(app)
