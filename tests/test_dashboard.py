from datetime import datetime, timedelta, timezone

import pytest

from app.extensions import db
from app.models import Movimentacao
from tests.ajudantes import criar_produto, erro, movimentar


def _hoje() -> str:
    return datetime.now(timezone.utc).date().isoformat()


def _cenario(cliente, dados, h_admin, h_admin_b):
    """P1: saldo 6 a R$2 (valor 12). P2: saldo 5 a R$10 (valor 50), em ruptura.
    P3 inativo. Empresa B com movimento próprio, que não pode aparecer."""
    p1 = criar_produto(cliente, h_admin, dados.categoria.id, sku="P1", nome="Cola")
    p2 = criar_produto(cliente, h_admin, dados.categoria.id, sku="P2", nome="Água", estoque_minimo=10)
    p3 = criar_produto(cliente, h_admin, dados.categoria.id, sku="P3", estoque_minimo=10)
    movimentar(cliente, h_admin, p1["id"], "ENTRADA", 10, custo_unitario=2.0)
    movimentar(cliente, h_admin, p1["id"], "SAIDA", 4)
    movimentar(cliente, h_admin, p2["id"], "ENTRADA", 5, custo_unitario=10.0)
    cliente.delete(f"/produtos/{p3['id']}", headers=h_admin)
    alheio = criar_produto(cliente, h_admin_b, dados.categoria_b.id, sku="B1")
    movimentar(cliente, h_admin_b, alheio["id"], "ENTRADA", 100, custo_unitario=50.0)
    movimentar(cliente, h_admin_b, alheio["id"], "SAIDA", 60)
    return p1, p2


def test_resumo_tem_o_formato_do_contrato(cliente, dados, h_admin):
    corpo = cliente.get("/dashboard/resumo", headers=h_admin).get_json()
    assert set(corpo) == {"periodo", "kpis", "serie_diaria", "valor_por_categoria",
                          "top_saidas", "alertas"}
    assert corpo["periodo"]["dias"] == 30
    assert corpo["periodo"]["ate"] == _hoje()
    assert len(corpo["serie_diaria"]) == 30
    assert corpo["serie_diaria"][-1] == {"data": _hoje(), "entradas": 0, "saidas": 0}


def test_resumo_soma_so_a_propria_empresa(cliente, dados, h_admin, h_admin_b):
    p1, p2 = _cenario(cliente, dados, h_admin, h_admin_b)
    corpo = cliente.get("/dashboard/resumo?dias=7", headers=h_admin).get_json()
    assert corpo["kpis"] == {"valor_estoque": 62.0, "produtos_ativos": 2,
                             "em_ruptura": 1, "movimentacoes": 3}
    assert corpo["serie_diaria"][-1] == {"data": _hoje(), "entradas": 15, "saidas": 4}
    assert corpo["valor_por_categoria"] == [{"categoria": "Bebidas", "valor": 62.0}]
    assert corpo["top_saidas"] == [{"produto_id": p1["id"], "nome": "Cola", "quantidade": 4}]
    assert [item["sku"] for item in corpo["alertas"]] == ["P2"]


def test_movimento_fora_do_periodo_nao_conta(cliente, dados, h_admin):
    produto = criar_produto(cliente, h_admin, dados.categoria.id)
    movimentar(cliente, h_admin, produto["id"], "ENTRADA", 10)
    antiga = movimentar(cliente, h_admin, produto["id"], "SAIDA", 3).get_json()
    registro = db.session.get(Movimentacao, antiga["id"])
    registro.criado_em = datetime.now(timezone.utc) - timedelta(days=40)
    db.session.commit()

    em_30 = cliente.get("/dashboard/resumo?dias=30", headers=h_admin).get_json()
    em_90 = cliente.get("/dashboard/resumo?dias=90", headers=h_admin).get_json()
    assert em_30["top_saidas"] == [] and em_30["kpis"]["movimentacoes"] == 1
    assert em_90["top_saidas"][0]["quantidade"] == 3 and em_90["kpis"]["movimentacoes"] == 2


@pytest.mark.parametrize("dias", ["0", "366", "abc"])
def test_periodo_invalido_responde_400(cliente, h_admin, dias):
    resposta = cliente.get(f"/dashboard/resumo?dias={dias}", headers=h_admin)
    assert resposta.status_code == 400
    assert erro(resposta)["campo"] == "dias"


def test_top_saidas_limita_a_cinco_em_ordem(cliente, dados, h_admin):
    for indice in range(7):
        produto = criar_produto(cliente, h_admin, dados.categoria.id, sku=f"S{indice}")
        movimentar(cliente, h_admin, produto["id"], "ENTRADA", 50)
        movimentar(cliente, h_admin, produto["id"], "SAIDA", indice + 1)
    corpo = cliente.get("/dashboard/resumo", headers=h_admin).get_json()
    assert [item["quantidade"] for item in corpo["top_saidas"]] == [7, 6, 5, 4, 3]


def test_dashboard_exige_token(cliente):
    assert cliente.get("/dashboard/resumo").status_code == 401
