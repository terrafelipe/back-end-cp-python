"""Saldo, ruptura e custo médio (RN-02, RN-06, RN-07).

O saldo lido pela API vem do cache `produto.saldo_atual`. `saldos()` recalcula
a partir do histórico: é a referência contra a qual o cache é testado.
"""

from decimal import ROUND_HALF_UP, Decimal

from app.models import Movimentacao, Produto, TipoMovimentacao

CENTAVO = Decimal("0.01")


def saldo_apos(saldo_atual: int, tipo: TipoMovimentacao, quantidade: int) -> int:
    """Saldo depois de uma movimentação.

    `AJUSTE` **define** o saldo em vez de somar a ele: a quantidade é sempre
    positiva (RN-03) e a correção precisa poder ir nos dois sentidos (RN-04).
    Na prática é a contagem de inventário.
    """
    if tipo is TipoMovimentacao.AJUSTE:
        return quantidade
    if tipo is TipoMovimentacao.ENTRADA:
        return saldo_atual + quantidade
    return saldo_atual - quantidade


def saldos(produto_ids: list[int]) -> dict[int, int]:
    """Saldo de vários produtos recalculado do histórico, numa única consulta."""
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
        apurado[movimentacao.produto_id] = saldo_apos(
            apurado[movimentacao.produto_id], movimentacao.tipo, movimentacao.quantidade
        )
    return apurado


def saldo(produto_id: int) -> int:
    return saldos([produto_id])[produto_id]


def em_ruptura(estoque_minimo: int, saldo_atual: int) -> bool:
    """RN-06 — saldo abaixo do mínimo sinaliza reposição."""
    return saldo_atual < estoque_minimo


def condicao_ruptura():
    """RN-06 em SQL, para filtrar e contar no banco. Mesmo critério de `em_ruptura`."""
    return Produto.saldo_atual < Produto.estoque_minimo


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
