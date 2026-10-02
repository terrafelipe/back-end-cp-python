import pytest

from app.services import estoque_service
from tests.ajudantes import criar_produto, movimentar


@pytest.fixture
def sem_historico(monkeypatch):
    """Falha se alguma leitura recalcular o saldo pelo histórico."""
    def proibido(*args, **kwargs):
        raise AssertionError("leitura recalculou o saldo pelo histórico")
    monkeypatch.setattr(estoque_service, "saldos", proibido)


def _cenario(cliente, dados, h_admin):
    """3 produtos em ruptura (A, B, C), 2 abastecidos (D, E) e 1 inativo em ruptura (Z)."""
    for sku, minimo, entrada in [("A", 10, 1), ("B", 10, 2), ("C", 10, 3),
                                 ("D", 1, 5), ("E", 1, 5), ("Z", 10, 1)]:
        produto = criar_produto(cliente, h_admin, dados.categoria.id, sku=sku, estoque_minimo=minimo)
        movimentar(cliente, h_admin, produto["id"], "ENTRADA", entrada)
        if sku == "Z":
            cliente.delete(f"/produtos/{produto['id']}", headers=h_admin)


@pytest.mark.parametrize("url", ["/estoque/alertas", "/produtos?em_ruptura=true",
                                 "/produtos", "/estoque/saldo"])
def test_leituras_nao_recalculam_o_historico(cliente, dados, h_admin, sem_historico, url):
    assert cliente.get(url, headers=h_admin).status_code == 200


def test_filtro_de_ruptura_pagina_no_banco(cliente, dados, h_admin):
    _cenario(cliente, dados, h_admin)
    corpo = cliente.get("/produtos?em_ruptura=true&por_pagina=2", headers=h_admin).get_json()
    assert (corpo["total"], corpo["total_paginas"]) == (3, 2)
    assert [item["sku"] for item in corpo["itens"]] == ["A", "B"]


def test_alertas_ignoram_produto_inativo(cliente, dados, h_admin):
    _cenario(cliente, dados, h_admin)
    corpo = cliente.get("/estoque/alertas", headers=h_admin).get_json()
    assert [item["sku"] for item in corpo["itens"]] == ["A", "B", "C"]
    assert all(item["em_ruptura"] for item in corpo["itens"])


def test_saldo_consolidado_traz_o_saldo_do_cache(cliente, dados, h_admin):
    _cenario(cliente, dados, h_admin)
    corpo = cliente.get("/estoque/saldo", headers=h_admin).get_json()
    assert {item["sku"]: item["saldo"] for item in corpo["itens"]} == {
        "A": 1, "B": 2, "C": 3, "D": 5, "E": 5,
    }
