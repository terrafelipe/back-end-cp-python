"""Os 11 passos do "Roteiro de validação" do README, sobre os dados do seed."""

import seed
from tests.ajudantes import erro


def _login(cliente, email, senha) -> dict:
    resposta = cliente.post("/auth/login", json={"email": email, "senha": senha})
    assert resposta.status_code == 200
    return {"Authorization": f"Bearer {resposta.get_json()['access_token']}"}


def test_roteiro_de_validacao_do_readme(cliente, banco):
    _, produtos = seed.povoar()

    # 1. Swagger lista as rotas
    paths = cliente.get("/swagger.json").get_json()["paths"]
    assert {"/produtos", "/dashboard/resumo", "/relatorios/reposicao"} <= set(paths)

    # 2 e 3. Login e identidade sem senha
    admin = _login(cliente, "admin@demo.com", "admin123")
    eu = cliente.get("/auth/me", headers=admin).get_json()
    assert eu["email"] == "admin@demo.com" and not any("senha" in k for k in eu)

    # 4. Produtos com saldo e ruptura
    lista = cliente.get("/produtos", headers=admin).get_json()
    assert lista["total"] == 8 and {"saldo", "em_ruptura"} <= set(lista["itens"][0])

    # 5. Três alertas
    assert cliente.get("/estoque/alertas", headers=admin).get_json()["total"] == 3

    # 6. Entrada sobe o saldo e recalcula o custo médio
    cola = produtos["BEB-COLA-350"]
    antes = cliente.get(f"/produtos/{cola.id}", headers=admin).get_json()
    resposta = cliente.post("/movimentacoes", headers=admin, json={
        "produto_id": cola.id, "tipo": "ENTRADA", "quantidade": 100, "custo_unitario": 9.99})
    assert resposta.status_code == 201
    depois = cliente.get(f"/produtos/{cola.id}", headers=admin).get_json()
    assert depois["saldo"] == antes["saldo"] + 100
    assert depois["preco_custo"] != antes["preco_custo"]

    # 7. Saída impossível → RN-02 com o saldo na mensagem
    resposta = cliente.post("/movimentacoes", headers=admin, json={
        "produto_id": cola.id, "tipo": "SAIDA", "quantidade": depois["saldo"] + 1})
    assert resposta.status_code == 422 and erro(resposta)["codigo"] == "RN-02"
    assert str(depois["saldo"]) in erro(resposta)["mensagem"]

    # 8. Histórico imutável → RN-04
    mov_id = cliente.get("/movimentacoes?por_pagina=1", headers=admin).get_json()["itens"][0]["id"]
    for metodo in (cliente.put, cliente.delete):
        resposta = metodo(f"/movimentacoes/{mov_id}", headers=admin)
        assert resposta.status_code == 405 and erro(resposta)["codigo"] == "RN-04"

    # 9. Papel do operador → RN-09 e RN-10
    operador = _login(cliente, "operador@demo.com", "operador123")
    resposta = cliente.post("/fornecedores", json={"nome": "Fornecedor X"}, headers=operador)
    assert resposta.status_code == 403 and erro(resposta)["codigo"] == "RN-09"
    resposta = cliente.delete(f"/produtos/{cola.id}", headers=operador)
    assert resposta.status_code == 403 and erro(resposta)["codigo"] == "RN-10"

    # 10. Outra empresa → 404
    nova = cliente.post("/auth/register", json={
        "empresa": "Outra Loja", "cnpj": "11.444.777/0001-61", "nome": "Bia",
        "email": "bia@outra.com", "senha": "senha123"}).get_json()
    outra = {"Authorization": f"Bearer {nova['access_token']}"}
    resposta = cliente.get(f"/produtos/{cola.id}", headers=outra)
    assert resposta.status_code == 404

    # 11. Envelope único
    assert set(erro(resposta)) == {"codigo", "mensagem", "campo"}
