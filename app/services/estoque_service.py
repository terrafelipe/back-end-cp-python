"""Saldo derivado do histórico, ruptura e custo médio (RN-02, RN-06, RN-07).

Não existe coluna de saldo em `produto`: o valor é sempre recalculado a
partir das movimentações, então não tem como divergir do histórico que o
originou.
"""

from decimal import ROUND_HALF_UP, Decimal

from app.models import Movimentacao, TipoMovimentacao

CENTAVO = Decimal("0.01")


def saldos(produto_ids: list[int]) -> dict[int, int]:
    """Saldo de vários produtos numa única consulta.

    `AJUSTE` **define** o saldo em vez de somar a ele. É a única leitura
    compatível com o modelo: a quantidade é sempre positiva (RN-03) e a
    correção precisa poder ir nos dois sentidos (RN-04) — o que um delta de
    sinal fixo não permitiria. Na prática é a contagem de inventário: o
    operador informa o que contou na prateleira.
    """
    apurado = {produto_id: 0 for produto_id in produto_ids}
    if not produto_ids:
        return apurado

    # Ordena por id, não por criado_em: o id é monotônico e não empata
    # quando duas movimentações caem no mesmo instante.
    historico = (
        Movimentacao.query.filter(Movimentacao.produto_id.in_(produto_ids))
        .order_by(Movimentacao.id)
        .all()
    )
    for movimentacao in historico:
        if movimentacao.tipo is TipoMovimentacao.AJUSTE:
            apurado[movimentacao.produto_id] = movimentacao.quantidade
        elif movimentacao.tipo is TipoMovimentacao.ENTRADA:
            apurado[movimentacao.produto_id] += movimentacao.quantidade
        else:
            apurado[movimentacao.produto_id] -= movimentacao.quantidade
    return apurado


def saldo(produto_id: int) -> int:
    return saldos([produto_id])[produto_id]


def em_ruptura(estoque_minimo: int, saldo_atual: int) -> bool:
    """RN-06 — saldo abaixo do mínimo sinaliza reposição."""
    return saldo_atual < estoque_minimo


def custo_medio_ponderado(
    saldo_atual: int,
    custo_atual: Decimal,
    quantidade: int,
    custo_unitario: Decimal | None,
) -> Decimal:
    """RN-07 — recalcula o custo médio a cada entrada.

    Pondera o que já estava em estoque pelo que está entrando. Entrada sem
    custo informado não altera o custo médio: não há valor novo a ponderar.
    """
    if custo_unitario is None:
        return custo_atual

    total = saldo_atual + quantidade
    if total <= 0:
        return Decimal(custo_unitario)

    valor_em_estoque = Decimal(saldo_atual) * Decimal(custo_atual)
    valor_entrando = Decimal(quantidade) * Decimal(custo_unitario)
    return ((valor_em_estoque + valor_entrando) / Decimal(total)).quantize(
        CENTAVO, rounding=ROUND_HALF_UP
    )
