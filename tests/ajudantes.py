"""Atalhos para montar cenários pela API nos testes."""


def criar_produto(cliente, cabecalho, categoria_id, sku="SKU-1", **extra) -> dict:
    corpo = {
        "sku": sku,
        "nome": extra.pop("nome", f"Produto {sku}"),
        "categoria_id": categoria_id,
        **extra,
    }
    resposta = cliente.post("/produtos", json=corpo, headers=cabecalho)
    assert resposta.status_code == 201, resposta.get_json()
    return resposta.get_json()


def movimentar(cliente, cabecalho, produto_id, tipo, quantidade, **extra):
    corpo = {"produto_id": produto_id, "tipo": tipo, "quantidade": quantidade, **extra}
    return cliente.post("/movimentacoes", json=corpo, headers=cabecalho)


def erro(resposta) -> dict:
    return resposta.get_json()["erro"]
