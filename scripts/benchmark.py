"""Mede alertas, produtos e dashboard com volume realista.

Uso:
    python scripts/benchmark.py
    python scripts/benchmark.py --produtos 500 --movimentacoes 20000 --repeticoes 20

Cria um SQLite temporário, popula direto pelo ORM (rápido, sem passar pelas
regras) e mede pelo test client do Flask, sem rede. Roda antes e depois das
otimizações do CP2; o resultado vai para docs/benchmark-cp2.md e o README.
"""

import argparse
import os
import random
import shutil
import statistics
import sys
import tempfile
import time
from datetime import timedelta
from decimal import Decimal
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

ROTAS = [
    ("/estoque/alertas", "/estoque/alertas?por_pagina=20"),
    ("/produtos?em_ruptura=true", "/produtos?em_ruptura=true&por_pagina=20"),
    ("/produtos", "/produtos?por_pagina=20"),
    ("/estoque/saldo", "/estoque/saldo?por_pagina=20"),
    ("/dashboard/resumo", "/dashboard/resumo?dias=30"),
]


def _argumentos():
    parser = argparse.ArgumentParser(description="Benchmark das leituras de estoque")
    parser.add_argument("--produtos", type=int, default=500)
    parser.add_argument("--movimentacoes", type=int, default=20_000)
    parser.add_argument("--repeticoes", type=int, default=20)
    return parser.parse_args()


def _popular(n_produtos: int, n_movimentacoes: int):
    """Empresa, admin, 5 categorias, produtos e 90 dias de histórico."""
    from sqlalchemy import insert

    from app.extensions import db
    from app.models import (
        Categoria, Empresa, Movimentacao, Produto, RoleUsuario, TipoMovimentacao, Usuario,
    )
    from app.models.base import agora_utc
    from app.security import gerar_hash

    sorteio = random.Random(42)
    empresa = Empresa(nome="Benchmark", cnpj="98.765.432/0001-98")
    db.session.add(empresa)
    db.session.flush()
    admin = Usuario(
        nome="Admin", email="admin@benchmark.com", senha_hash=gerar_hash("benchmark"),
        role=RoleUsuario.ADMIN, empresa_id=empresa.id,
    )
    categorias = [Categoria(nome=f"Categoria {i}", empresa_id=empresa.id) for i in range(5)]
    db.session.add_all([admin, *categorias])
    db.session.flush()

    produtos = [
        Produto(
            sku=f"BEN-{i:04d}", nome=f"Produto {i:04d}",
            categoria_id=sorteio.choice(categorias).id,
            preco_custo=Decimal("0"), preco_venda=Decimal(sorteio.randint(2, 80)),
            estoque_minimo=sorteio.randint(5, 50), empresa_id=empresa.id,
        )
        for i in range(n_produtos)
    ]
    db.session.add_all(produtos)
    db.session.flush()

    saldos = {produto.id: 0 for produto in produtos}
    inicio = agora_utc() - timedelta(days=90)
    passo = timedelta(days=90) / n_movimentacoes
    linhas = []
    for k in range(n_movimentacoes):
        produto = sorteio.choice(produtos)
        if saldos[produto.id] < 5 or sorteio.random() < 0.3:
            quantidade = sorteio.randint(10, 60)
            tipo, custo = TipoMovimentacao.ENTRADA, Decimal(sorteio.randint(100, 5000)) / 100
            saldos[produto.id] += quantidade
            # Aproximação: o benchmark mede leitura, não o custo médio.
            produto.preco_custo = custo
        else:
            quantidade = sorteio.randint(1, min(saldos[produto.id], 10))
            tipo, custo = TipoMovimentacao.SAIDA, None
            saldos[produto.id] -= quantidade
        linhas.append({
            "produto_id": produto.id, "tipo": tipo, "quantidade": quantidade,
            "custo_unitario": custo, "usuario_id": admin.id, "criado_em": inicio + passo * k,
        })
    db.session.execute(insert(Movimentacao), linhas)

    # Antes do CP2 a coluna de cache não existe; depois, precisa bater com o histórico.
    if hasattr(Produto, "saldo_atual"):
        for produto in produtos:
            produto.saldo_atual = saldos[produto.id]
    db.session.commit()
    return admin


def main() -> int:
    args = _argumentos()
    pasta = Path(tempfile.mkdtemp(prefix="benchmark-estoque-"))
    # Config lê o ambiente na importação: tudo definido antes de importar `app`.
    os.environ["DATABASE_URL"] = f"sqlite:///{(pasta / 'benchmark.db').as_posix()}"
    os.environ["AUTO_MIGRATE"] = "0"
    os.environ["FLASK_DEBUG"] = "1"
    os.environ["SQLALCHEMY_ECHO"] = "0"

    from flask_jwt_extended import create_access_token

    from app import create_app
    from app.extensions import db

    app = create_app()
    try:
        with app.app_context():
            db.create_all()
            admin = _popular(args.produtos, args.movimentacoes)
            cabecalho = {"Authorization": f"Bearer {create_access_token(identity=str(admin.id))}"}
            cliente = app.test_client()

            print(f"{args.produtos} produtos, {args.movimentacoes} movimentações, "
                  f"{args.repeticoes} repetições\n")
            print("| rota | mediana (ms) | p95 (ms) |")
            print("|---|---|---|")
            for nome, url in ROTAS:
                # A primeira chamada aquece o cache e diz se a rota já existe.
                if cliente.get(url, headers=cabecalho).status_code == 404:
                    print(f"| `{nome}` | não existe | — |")
                    continue
                tempos = []
                for _ in range(args.repeticoes):
                    inicio = time.perf_counter()
                    resposta = cliente.get(url, headers=cabecalho)
                    tempos.append((time.perf_counter() - inicio) * 1000)
                    assert resposta.status_code == 200, resposta.get_json()
                p95 = statistics.quantiles(tempos, n=20)[-1] if len(tempos) > 1 else tempos[0]
                print(f"| `{nome}` | {statistics.median(tempos):.1f} | {p95:.1f} |")

            db.session.remove()
            db.engine.dispose()
    finally:
        shutil.rmtree(pasta, ignore_errors=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
