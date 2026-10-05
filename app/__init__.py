"""Application factory do Gestor de Estoque."""

import logging
from pathlib import Path

from flask import Flask

from app.config import Config, problemas_de_seguranca
from app.extensions import api, cors, db, jwt, migrate

logger = logging.getLogger(__name__)


def create_app(config_object: type[Config] = Config) -> Flask:
    """Cria e configura a instância do Flask."""
    app = Flask(__name__)
    app.config.from_object(config_object)
    # Antes de qualquer registro: falhar aqui não deixa a Api global pela metade.
    problemas = problemas_de_seguranca(app.config)
    if problemas:
        raise RuntimeError(
            "A aplicação não sobe com FLASK_DEBUG=0 sem chaves próprias:\n- "
            + "\n- ".join(problemas)
        )
    # Mesma razão do RESTX_JSON: vale para o `jsonify` do próprio Flask,
    # usado pelos tratadores de erro fora do flask-restx.
    app.json.ensure_ascii = False

    _registrar_extensoes(app)
    _registrar_tratadores_de_erro(app)
    _registrar_namespaces(app)

    return app


def aplicar_migrations(app: Flask) -> None:
    """Aplica as migrations pendentes do Alembic.

    Chamado por `app.py` e por `seed.py`, para que um clone limpo — sem banco
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
    # Permite que o frontend da próxima entrega, servido em outra porta,
    # consuma a API sem esbarrar na política de mesma origem do navegador.
    origens = [o.strip() for o in app.config["CORS_ORIGINS"].split(",") if o.strip()]
    cors.init_app(app, resources={r"/*": {"origins": origens}})

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
    from app.controllers.auth import ns as auth_ns
    from app.controllers.categorias import ns as categorias_ns
    from app.controllers.dashboard import ns as dashboard_ns
    from app.controllers.estoque import ns as estoque_ns
    from app.controllers.fornecedores import ns as fornecedores_ns
    from app.controllers.health import ns as health_ns
    from app.controllers.movimentacoes import ns as movimentacoes_ns
    from app.controllers.produtos import ns as produtos_ns
    from app.controllers.relatorios import ns as relatorios_ns
    from app.controllers.usuarios import ns as usuarios_ns

    api.add_namespace(health_ns, path="/health")
    api.add_namespace(auth_ns, path="/auth")
    api.add_namespace(usuarios_ns, path="/usuarios")
    api.add_namespace(categorias_ns, path="/categorias")
    api.add_namespace(fornecedores_ns, path="/fornecedores")
    api.add_namespace(produtos_ns, path="/produtos")
    api.add_namespace(movimentacoes_ns, path="/movimentacoes")
    api.add_namespace(estoque_ns, path="/estoque")
    api.add_namespace(dashboard_ns, path="/dashboard")
    api.add_namespace(relatorios_ns, path="/relatorios")

    api.init_app(app)
