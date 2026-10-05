import json

from app.models import RelatorioIA
from tests.ajudantes import criar_produto, erro, movimentar


def _produto(cliente, h, categoria_id, sku, minimo, entrada, saida=0, **extra):
    produto = criar_produto(cliente, h, categoria_id, sku=sku, estoque_minimo=minimo, **extra)
    if entrada:
        movimentar(cliente, h, produto["id"], "ENTRADA", entrada, custo_unitario=2.0)
    if saida:
        movimentar(cliente, h, produto["id"], "SAIDA", saida)
    return produto


def test_sem_candidatos_gera_relatorio_vazio_por_regras(cliente, dados, h_admin):
    _produto(cliente, h_admin, dados.categoria.id, "OK", minimo=5, entrada=100)
    resposta = cliente.post("/relatorios/reposicao", headers=h_admin)
    assert resposta.status_code == 201
    corpo = resposta.get_json()
    assert corpo["origem"] == "REGRAS" and corpo["modelo"] is None
    assert corpo["resultado"] == {"resumo": "Nenhum produto precisa de reposição agora.",
                                  "prioridades": []}


def test_regras_ordenam_por_dias_ate_acabar(cliente, dados, h_admin):
    _produto(cliente, h_admin, dados.categoria.id, "A", minimo=10, entrada=10, saida=10)   # saldo 0
    _produto(cliente, h_admin, dados.categoria.id, "B", minimo=10, entrada=30, saida=26)   # 4 → 4,6 dias
    _produto(cliente, h_admin, dados.categoria.id, "C", minimo=5, entrada=170, saida=120)  # 50 → 12,5 dias
    _produto(cliente, h_admin, dados.categoria.id, "D", minimo=5, entrada=100)             # sem saída
    corpo = cliente.post("/relatorios/reposicao", headers=h_admin).get_json()
    prioridades = corpo["resultado"]["prioridades"]
    assert [(p["sku"], p["quantidade_sugerida"]) for p in prioridades] == [
        ("A", 20), ("B", 22), ("C", 70),
    ]
    assert prioridades[0]["motivo"] == "Saldo 0 abaixo do mínimo de 10."
    assert prioridades[2]["motivo"] == "Estoque para cerca de 12,5 dias no ritmo atual."
    assert corpo["resultado"]["resumo"] == (
        "3 produto(s) precisam de reposição; 2 já abaixo do mínimo."
    )


def test_produto_inativo_fica_fora_do_relatorio(cliente, dados, h_admin):
    inativo = _produto(cliente, h_admin, dados.categoria.id, "Z", minimo=10, entrada=1)
    cliente.delete(f"/produtos/{inativo['id']}", headers=h_admin)
    corpo = cliente.post("/relatorios/reposicao", headers=h_admin).get_json()
    assert corpo["resultado"]["prioridades"] == []


def test_ultimo_responde_404_antes_do_primeiro(cliente, h_admin):
    resposta = cliente.get("/relatorios/reposicao/ultimo", headers=h_admin)
    assert resposta.status_code == 404
    assert erro(resposta)["codigo"] == "HTTP-404"


def test_ultimo_e_historico_trazem_o_mais_recente_primeiro(cliente, dados, h_admin):
    cliente.post("/relatorios/reposicao", headers=h_admin)
    segundo = cliente.post("/relatorios/reposicao", headers=h_admin).get_json()
    assert cliente.get("/relatorios/reposicao/ultimo", headers=h_admin).get_json()["id"] == segundo["id"]
    lista = cliente.get("/relatorios/reposicao", headers=h_admin).get_json()
    assert lista["total"] == 2 and lista["itens"][0]["id"] == segundo["id"]


def test_relatorio_de_outra_empresa_nao_aparece(cliente, dados, h_admin, h_admin_b):
    _produto(cliente, h_admin_b, dados.categoria_b.id, "B-1", minimo=10, entrada=1)
    cliente.post("/relatorios/reposicao", headers=h_admin_b)
    assert cliente.get("/relatorios/reposicao/ultimo", headers=h_admin).status_code == 404
    assert cliente.get("/relatorios/reposicao", headers=h_admin).get_json()["total"] == 0
    proprio = cliente.post("/relatorios/reposicao", headers=h_admin).get_json()
    assert proprio["resultado"]["prioridades"] == []


def test_relatorio_exige_token(cliente):
    assert cliente.post("/relatorios/reposicao").status_code == 401


def test_entrada_salva_so_tem_os_campos_permitidos(cliente, dados, h_admin):
    _produto(cliente, h_admin, dados.categoria.id, "A", minimo=10, entrada=1)
    cliente.post("/relatorios/reposicao", headers=h_admin)
    entrada = RelatorioIA.query.one().entrada
    assert set(entrada["produtos"][0]) == {
        "sku", "nome", "categoria", "saldo", "estoque_minimo", "consumo_30d",
        "custo_medio", "dias_ate_acabar", "quantidade_sugerida",
    }
    texto = json.dumps(entrada, ensure_ascii=False)
    for proibido in ("admin@a.com", dados.empresa.cnpj, dados.empresa.nome):
        assert proibido not in texto
