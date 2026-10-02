import pytest

from tests.ajudantes import criar_produto, erro, movimentar


def test_sku_repetido_na_mesma_empresa_rn01(cliente, dados, h_admin):
    criar_produto(cliente, h_admin, dados.categoria.id, sku="BEB-1")
    resposta = cliente.post(
        "/produtos",
        json={"sku": "BEB-1", "nome": "Outro", "categoria_id": dados.categoria.id},
        headers=h_admin,
    )
    assert resposta.status_code == 422
    assert erro(resposta)["codigo"] == "RN-01"
    assert erro(resposta)["campo"] == "sku"


def test_mesmo_sku_em_outra_empresa_e_permitido(cliente, dados, h_admin, h_admin_b):
    criar_produto(cliente, h_admin, dados.categoria.id, sku="BEB-1")
    criar_produto(cliente, h_admin_b, dados.categoria_b.id, sku="BEB-1")


def test_saida_maior_que_saldo_rn02(cliente, dados, h_admin):
    produto = criar_produto(cliente, h_admin, dados.categoria.id)
    movimentar(cliente, h_admin, produto["id"], "ENTRADA", 10)
    resposta = movimentar(cliente, h_admin, produto["id"], "SAIDA", 11)
    assert resposta.status_code == 422
    assert erro(resposta) == {
        "codigo": "RN-02",
        "mensagem": "Saída de 11 unidades excede o saldo disponível de 10 unidades.",
        "campo": "quantidade",
    }


@pytest.mark.parametrize("quantidade", [0, -5])
def test_quantidade_nao_positiva_e_recusada_rn03(cliente, dados, h_admin, quantidade):
    produto = criar_produto(cliente, h_admin, dados.categoria.id)
    resposta = movimentar(cliente, h_admin, produto["id"], "ENTRADA", quantidade)
    assert resposta.status_code == 400
    assert erro(resposta)["campo"] == "quantidade"


@pytest.mark.parametrize("metodo", ["put", "delete"])
def test_movimentacao_e_imutavel_rn04(cliente, dados, h_admin, metodo):
    produto = criar_produto(cliente, h_admin, dados.categoria.id)
    mov = movimentar(cliente, h_admin, produto["id"], "ENTRADA", 5).get_json()
    resposta = getattr(cliente, metodo)(f"/movimentacoes/{mov['id']}", headers=h_admin)
    assert resposta.status_code == 405
    assert erro(resposta)["codigo"] == "RN-04"


def test_excluir_produto_inativa_rn05(cliente, dados, h_admin):
    produto = criar_produto(cliente, h_admin, dados.categoria.id)
    movimentar(cliente, h_admin, produto["id"], "ENTRADA", 5)
    assert cliente.delete(f"/produtos/{produto['id']}", headers=h_admin).status_code == 204
    detalhe = cliente.get(f"/produtos/{produto['id']}", headers=h_admin).get_json()
    assert detalhe["ativo"] is False
    assert cliente.get("/produtos", headers=h_admin).get_json()["total"] == 0


def test_produto_inativo_nao_aceita_movimentacao(cliente, dados, h_admin):
    produto = criar_produto(cliente, h_admin, dados.categoria.id)
    cliente.delete(f"/produtos/{produto['id']}", headers=h_admin)
    resposta = movimentar(cliente, h_admin, produto["id"], "ENTRADA", 1)
    assert resposta.status_code == 422
    assert erro(resposta)["campo"] == "produto_id"


def test_alertas_listam_so_abaixo_do_minimo_rn06(cliente, dados, h_admin):
    baixo = criar_produto(cliente, h_admin, dados.categoria.id, sku="A", estoque_minimo=10)
    no_limite = criar_produto(cliente, h_admin, dados.categoria.id, sku="B", estoque_minimo=10)
    movimentar(cliente, h_admin, baixo["id"], "ENTRADA", 3)
    movimentar(cliente, h_admin, no_limite["id"], "ENTRADA", 10)
    corpo = cliente.get("/estoque/alertas", headers=h_admin).get_json()
    assert [item["sku"] for item in corpo["itens"]] == ["A"]
    assert corpo["itens"][0]["saldo"] == 3
    assert corpo["itens"][0]["em_ruptura"] is True


def test_custo_medio_ponderado_rn07(cliente, dados, h_admin):
    produto = criar_produto(cliente, h_admin, dados.categoria.id)
    movimentar(cliente, h_admin, produto["id"], "ENTRADA", 10, custo_unitario=2.0)
    movimentar(cliente, h_admin, produto["id"], "ENTRADA", 30, custo_unitario=4.0)
    detalhe = cliente.get(f"/produtos/{produto['id']}", headers=h_admin).get_json()
    assert float(detalhe["preco_custo"]) == 3.5


def test_ajuste_define_o_saldo(cliente, dados, h_admin):
    produto = criar_produto(cliente, h_admin, dados.categoria.id)
    movimentar(cliente, h_admin, produto["id"], "ENTRADA", 10)
    movimentar(cliente, h_admin, produto["id"], "AJUSTE", 4)
    movimentar(cliente, h_admin, produto["id"], "ENTRADA", 1)
    assert cliente.get(f"/produtos/{produto['id']}", headers=h_admin).get_json()["saldo"] == 5


def test_produto_de_outra_empresa_responde_404_rn08(cliente, dados, h_admin, h_admin_b):
    alheio = criar_produto(cliente, h_admin_b, dados.categoria_b.id)
    assert cliente.get(f"/produtos/{alheio['id']}", headers=h_admin).status_code == 404
    assert movimentar(cliente, h_admin, alheio["id"], "ENTRADA", 1).status_code == 404


def test_categoria_de_outra_empresa_e_recusada_no_produto(cliente, dados, h_admin):
    resposta = cliente.post(
        "/produtos",
        json={"sku": "X", "nome": "Produto X", "categoria_id": dados.categoria_b.id},
        headers=h_admin,
    )
    assert resposta.status_code == 422
    assert erro(resposta)["campo"] == "categoria_id"


def test_operador_nao_cria_fornecedor_rn09(cliente, h_operador):
    resposta = cliente.post("/fornecedores", json={"nome": "Fornecedor"}, headers=h_operador)
    assert resposta.status_code == 403
    assert erro(resposta)["codigo"] == "RN-09"


def test_operador_nao_define_preco_de_venda_rn09(cliente, dados, h_operador):
    resposta = cliente.post(
        "/produtos",
        json={"sku": "X", "nome": "Produto X", "categoria_id": dados.categoria.id, "preco_venda": 9.9},
        headers=h_operador,
    )
    assert resposta.status_code == 403
    assert erro(resposta)["codigo"] == "RN-09"


def test_operador_cria_produto_sem_preco_e_movimenta(cliente, dados, h_operador):
    produto = criar_produto(cliente, h_operador, dados.categoria.id)
    assert movimentar(cliente, h_operador, produto["id"], "ENTRADA", 2).status_code == 201


def test_operador_nao_exclui_produto_rn10(cliente, dados, h_admin, h_operador):
    produto = criar_produto(cliente, h_admin, dados.categoria.id)
    resposta = cliente.delete(f"/produtos/{produto['id']}", headers=h_operador)
    assert resposta.status_code == 403
    assert erro(resposta)["codigo"] == "RN-10"


def test_listagem_usa_envelope_paginado(cliente, dados, h_admin):
    for sku in ("A", "B", "C"):
        criar_produto(cliente, h_admin, dados.categoria.id, sku=sku)
    corpo = cliente.get("/produtos?pagina=2&por_pagina=2", headers=h_admin).get_json()
    assert {k: corpo[k] for k in ("pagina", "por_pagina", "total", "total_paginas")} == {
        "pagina": 2, "por_pagina": 2, "total": 3, "total_paginas": 2,
    }
    assert len(corpo["itens"]) == 1


def test_por_pagina_acima_do_limite_responde_400(cliente, h_admin):
    resposta = cliente.get("/produtos?por_pagina=101", headers=h_admin)
    assert resposta.status_code == 400
    assert erro(resposta)["campo"] == "por_pagina"


def test_filtro_em_ruptura_falso_traz_so_os_abastecidos(cliente, dados, h_admin):
    baixo = criar_produto(cliente, h_admin, dados.categoria.id, sku="A", estoque_minimo=10)
    cheio = criar_produto(cliente, h_admin, dados.categoria.id, sku="B", estoque_minimo=1)
    movimentar(cliente, h_admin, baixo["id"], "ENTRADA", 1)
    movimentar(cliente, h_admin, cheio["id"], "ENTRADA", 5)
    corpo = cliente.get("/produtos?em_ruptura=false", headers=h_admin).get_json()
    assert [item["sku"] for item in corpo["itens"]] == ["B"]


def test_rota_inexistente_responde_404_no_envelope(cliente):
    resposta = cliente.get("/nao-existe")
    assert resposta.status_code == 404
    assert erro(resposta)["codigo"] == "HTTP-404"
