import os
import subprocess
import sys
from pathlib import Path

import pytest

from app import create_app
from app.config import SEGREDO_DEV, problemas_de_seguranca
from tests.conftest import ConfigTeste

RAIZ = Path(__file__).resolve().parent.parent
FORTE = "k" * 40


def test_debug_ligado_aceita_chave_de_desenvolvimento():
    config = {"DEBUG": True, "SECRET_KEY": SEGREDO_DEV, "JWT_SECRET_KEY": SEGREDO_DEV}
    assert problemas_de_seguranca(config) == []


def test_sem_debug_recusa_chaves_de_desenvolvimento_ou_vazias():
    problemas = problemas_de_seguranca(
        {"DEBUG": False, "SECRET_KEY": SEGREDO_DEV, "JWT_SECRET_KEY": ""}
    )
    assert len(problemas) == 2
    assert problemas[0].startswith("SECRET_KEY") and problemas[1].startswith("JWT_SECRET_KEY")


def test_sem_debug_recusa_chave_curta():
    problemas = problemas_de_seguranca({"DEBUG": False, "SECRET_KEY": "curta", "JWT_SECRET_KEY": FORTE})
    assert len(problemas) == 1


def test_sem_debug_recusa_valor_do_env_example():
    problemas = problemas_de_seguranca({
        "DEBUG": False,
        "SECRET_KEY": "troque-esta-chave-em-qualquer-ambiente-que-nao-seja-local",
        "JWT_SECRET_KEY": FORTE,
    })
    assert len(problemas) == 1


def test_sem_debug_aceita_chaves_fortes():
    assert problemas_de_seguranca({"DEBUG": False, "SECRET_KEY": FORTE, "JWT_SECRET_KEY": FORTE}) == []


def test_create_app_nao_sobe_sem_chaves():
    class ConfigProducaoSemChave(ConfigTeste):
        SECRET_KEY = SEGREDO_DEV
        JWT_SECRET_KEY = SEGREDO_DEV

    with pytest.raises(RuntimeError, match="SECRET_KEY"):
        create_app(ConfigProducaoSemChave)


def test_app_py_falha_com_mensagem_clara():
    env = {**os.environ, "FLASK_DEBUG": "0", "SECRET_KEY": "", "JWT_SECRET_KEY": "",
           "AUTO_MIGRATE": "0", "DATABASE_URL": "sqlite://", "PYTHONIOENCODING": "utf-8"}
    resultado = subprocess.run(
        [sys.executable, "app.py"], cwd=RAIZ, env=env, capture_output=True,
        text=True, encoding="utf-8", errors="replace", timeout=30,
    )
    assert resultado.returncode == 1
    assert "SECRET_KEY" in resultado.stderr
    assert "Traceback" not in resultado.stderr


def test_cors_aceita_o_front_local(cliente):
    resposta = cliente.get("/health", headers={"Origin": "http://localhost:5173"})
    assert resposta.headers.get("Access-Control-Allow-Origin") == "http://localhost:5173"


def test_cors_recusa_origem_desconhecida(cliente):
    resposta = cliente.get("/health", headers={"Origin": "http://malicioso.example"})
    assert "Access-Control-Allow-Origin" not in resposta.headers
