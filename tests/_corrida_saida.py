"""Duas saídas simultâneas do saldo inteiro, em threads e banco em arquivo.

Rodado em subprocesso por test_concorrencia.py (a app dos testes usa banco em
memória, que não serve para threads). Imprime o resultado em JSON.
"""

import json
import sys
import threading
import time

from app import create_app
from app.config import Config
from app.extensions import db
from app.models import Categoria, Empresa, Produto, RoleUsuario, Usuario
from app.services import estoque_service, movimentacao_service


class ConfigCorrida(Config):
    TESTING = True
    AUTO_MIGRATE = False
    SQLALCHEMY_DATABASE_URI = "sqlite:///" + sys.argv[1].replace("\\", "/")


app = create_app(ConfigCorrida)
with app.app_context():
    db.create_all()
    empresa = Empresa(nome="E", cnpj="00000000000100")
    db.session.add(empresa)
    db.session.flush()
    usuario = Usuario(nome="u", email="u@x.com", senha_hash="x",
                      role=RoleUsuario.ADMIN, empresa_id=empresa.id)
    categoria = Categoria(nome="c", empresa_id=empresa.id)
    db.session.add_all([usuario, categoria])
    db.session.flush()
    produto = Produto(sku="A", nome="A", categoria_id=categoria.id, empresa_id=empresa.id)
    db.session.add(produto)
    db.session.commit()
    movimentacao_service.registrar(usuario, {"produto_id": produto.id, "tipo": "ENTRADA", "quantidade": 5})
    uid, pid = usuario.id, produto.id

# Alarga a janela entre ler o saldo e gravar o novo.
original = estoque_service.saldo_apos
estoque_service.saldo_apos = lambda *a: (time.sleep(0.5), original(*a))[1]

resultados = []


def vender():
    with app.app_context():
        u = db.session.get(Usuario, uid)
        try:
            movimentacao_service.registrar(u, {"produto_id": pid, "tipo": "SAIDA", "quantidade": 5})
            resultados.append("ok")
        except Exception as erro:  # noqa: BLE001
            resultados.append(getattr(erro, "codigo", type(erro).__name__))


threads = [threading.Thread(target=vender) for _ in range(2)]
for t in threads:
    t.start()
for t in threads:
    t.join()

with app.app_context():
    print(json.dumps({
        "resultados": sorted(resultados),
        "cache": db.session.get(Produto, pid).saldo_atual,
        "historico": estoque_service.saldo(pid),
    }))
