from datetime import datetime, timedelta, timezone

import seed
from app.services import estoque_service


def test_plano_e_deterministico_e_cobre_60_dias():
    agora = datetime(2026, 10, 6, 12, tzinfo=timezone.utc)
    plano = seed.plano_de_movimentacoes(agora)
    assert plano == seed.plano_de_movimentacoes(agora)
    datas = [passo["criado_em"] for passo in plano]
    assert max(datas) < agora
    assert agora - min(datas) >= timedelta(days=60)
    assert {passo["tipo"] for passo in plano} == {"ENTRADA", "SAIDA", "AJUSTE"}


def test_seed_deixa_tres_em_ruptura_e_cache_igual_ao_historico(banco):
    _, produtos = seed.povoar()
    em_ruptura = sorted(p.sku for p in produtos.values() if p.saldo_atual < p.estoque_minimo)
    assert em_ruptura == ["BEB-AGUA-500", "LIM-SABAO-1L", "MER-FEIJAO-1KG"]
    derivado = estoque_service.saldos([p.id for p in produtos.values()])
    assert {p.id: p.saldo_atual for p in produtos.values()} == derivado
