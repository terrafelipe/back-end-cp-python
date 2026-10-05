"""Fixtures compartilhadas pelos testes.

Uma única app por sessão (a `Api` do flask-restx é global e não aceita
registrar os namespaces duas vezes), banco SQLite em memória recriado a cada
teste, duas empresas e cabeçalhos de autenticação por papel.
"""

import urllib.request
from types import SimpleNamespace

import bcrypt
import pytest
from flask_jwt_extended import create_access_token

from app import create_app
from app.config import Config
from app.extensions import db
from app.models import Categoria, Empresa, RoleUsuario, Usuario
from app.security import gerar_hash


class ConfigTeste(Config):
    TESTING = True
    DEBUG = False
    SQLALCHEMY_DATABASE_URI = "sqlite://"
    SQLALCHEMY_ECHO = False
    AUTO_MIGRATE = False
    SECRET_KEY = "segredo-de-teste-" + "x" * 32
    JWT_SECRET_KEY = "jwt-de-teste-" + "y" * 32
    # Sem chave: nenhum teste chama a LLM, a não ser que peça (fixture com_chave).
    GROQ_API_KEY = ""
    GROQ_MODEL = "modelo-de-teste"
    LLM_TIMEOUT_S = 1


@pytest.fixture(scope="session", autouse=True)
def _bcrypt_rapido():
    """Custo 4 em vez de 12: o hash deixa de dominar o tempo da suíte."""
    original = bcrypt.gensalt
    with pytest.MonkeyPatch.context() as mp:
        mp.setattr(
            bcrypt, "gensalt", lambda rounds=4, prefix=b"2b": original(rounds, prefix)
        )
        yield


@pytest.fixture(autouse=True)
def _sem_rede(monkeypatch):
    """Rede de segurança: nenhum teste fala com a internet."""
    def bloqueado(*args, **kwargs):
        raise AssertionError("teste tentou acessar a rede")
    monkeypatch.setattr(urllib.request, "urlopen", bloqueado)


@pytest.fixture(scope="session")
def app():
    return create_app(ConfigTeste)


@pytest.fixture(autouse=True)
def banco(app):
    with app.app_context():
        db.create_all()
        yield db
        db.session.remove()
        db.drop_all()


@pytest.fixture
def cliente(app):
    return app.test_client()


def _usuario(empresa: Empresa, email: str, role: RoleUsuario) -> Usuario:
    usuario = Usuario(
        nome=email.split("@")[0],
        email=email,
        senha_hash=gerar_hash("senha123"),
        role=role,
        empresa_id=empresa.id,
    )
    db.session.add(usuario)
    return usuario


@pytest.fixture
def dados(banco):
    """Empresa A (admin, operador, categoria) e empresa B (admin, categoria)."""
    empresa = Empresa(nome="Empresa A", cnpj="12.345.678/0001-95")
    empresa_b = Empresa(nome="Empresa B", cnpj="11.222.333/0001-81")
    db.session.add_all([empresa, empresa_b])
    db.session.flush()

    admin = _usuario(empresa, "admin@a.com", RoleUsuario.ADMIN)
    operador = _usuario(empresa, "operador@a.com", RoleUsuario.OPERADOR)
    admin_b = _usuario(empresa_b, "admin@b.com", RoleUsuario.ADMIN)
    categoria = Categoria(nome="Bebidas", empresa_id=empresa.id)
    categoria_b = Categoria(nome="Bebidas", empresa_id=empresa_b.id)
    db.session.add_all([categoria, categoria_b])
    db.session.commit()

    return SimpleNamespace(
        empresa=empresa,
        empresa_b=empresa_b,
        admin=admin,
        operador=operador,
        admin_b=admin_b,
        categoria=categoria,
        categoria_b=categoria_b,
    )


def _cabecalho(usuario: Usuario) -> dict:
    return {"Authorization": f"Bearer {create_access_token(identity=str(usuario.id))}"}


@pytest.fixture
def h_admin(dados):
    return _cabecalho(dados.admin)


@pytest.fixture
def h_operador(dados):
    return _cabecalho(dados.operador)


@pytest.fixture
def h_admin_b(dados):
    return _cabecalho(dados.admin_b)
