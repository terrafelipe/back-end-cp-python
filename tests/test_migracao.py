"""Backfill de `saldo_atual` num banco que já tem histórico.

Roda em subprocesso: precisa de outra app, apontada para um arquivo SQLite
temporário, e a `Api` do flask-restx só aceita uma app por processo.
"""

import ast
import os
import subprocess
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent

SCRIPT = r'''
import sys
from flask_migrate import downgrade, upgrade
from sqlalchemy import text
from app import create_app
from app.extensions import db

pasta = sys.argv[1]
app = create_app()
with app.app_context():
    upgrade(directory=pasta, revision="1abc8de16adf")
    s = db.session
    s.execute(text("INSERT INTO empresa (id, nome, cnpj, plano, criado_em) VALUES (1, 'E', '1', 'BASICO', '2026-01-01')"))
    s.execute(text("INSERT INTO usuario (id, nome, email, senha_hash, role, ativo, empresa_id, criado_em) VALUES (1, 'U', 'u@x.com', 'h', 'ADMIN', 1, 1, '2026-01-01')"))
    s.execute(text("INSERT INTO categoria (id, nome, empresa_id) VALUES (1, 'C', 1)"))
    for pid in (1, 2, 3):
        s.execute(text("INSERT INTO produto (id, sku, nome, categoria_id, preco_custo, preco_venda, estoque_minimo, unidade, ativo, empresa_id, criado_em) VALUES (:id, :sku, 'P', 1, 0, 0, 0, 'UN', 1, 1, '2026-01-01')"), {"id": pid, "sku": f"S{pid}"})
    movimentos = [(1, "ENTRADA", 10), (1, "SAIDA", 3), (2, "ENTRADA", 5), (2, "AJUSTE", 2), (2, "ENTRADA", 4)]
    for mid, (pid, tipo, qtd) in enumerate(movimentos, start=1):
        s.execute(text("INSERT INTO movimentacao (id, produto_id, tipo, quantidade, usuario_id, criado_em) VALUES (:m, :p, :t, :q, 1, '2026-01-02')"), {"m": mid, "p": pid, "t": tipo, "q": qtd})
    s.commit()
    upgrade(directory=pasta)
    antes_do_downgrade = dict(s.execute(text("SELECT id, saldo_atual FROM produto ORDER BY id")).all())
    s.commit()
    downgrade(directory=pasta, revision="1abc8de16adf")
    upgrade(directory=pasta)
    depois = dict(s.execute(text("SELECT id, saldo_atual FROM produto ORDER BY id")).all())
    fk = s.execute(text("PRAGMA foreign_keys")).scalar()
    print(repr((antes_do_downgrade, depois, fk)))
'''


def test_migration_preenche_saldo_pelo_historico(tmp_path):
    banco = tmp_path / "migracao.db"
    env = {
        **os.environ,
        "DATABASE_URL": f"sqlite:///{banco.as_posix()}",
        "AUTO_MIGRATE": "0",
        "FLASK_DEBUG": "1",
        "SQLALCHEMY_ECHO": "0",
        "PYTHONIOENCODING": "utf-8",
    }
    resultado = subprocess.run(
        [sys.executable, "-c", SCRIPT, str(RAIZ / "migrations")],
        cwd=RAIZ, env=env, capture_output=True, text=True,
        encoding="utf-8", errors="replace", timeout=120,
    )
    assert resultado.returncode == 0, resultado.stderr
    antes, depois, fk = ast.literal_eval(resultado.stdout.strip().splitlines()[-1])
    assert antes == {1: 7, 2: 6, 3: 0}
    assert depois == antes
    assert fk == 1
