"""Resumo do dashboard: tudo o que a tela inicial mostra, em uma requisição.

Cada bloco é uma agregação no banco (SUM/COUNT/GROUP BY) sobre o cache de
saldo e as movimentações do período; nada percorre o histórico em Python.
Os dias são contados em UTC, o fuso em que as datas são gravadas.
"""

from datetime import datetime, time, timedelta, timezone
from decimal import ROUND_HALF_UP, Decimal

from sqlalchemy import case, func

from app.errors import RequisicaoInvalida
from app.extensions import db
from app.models import Categoria, Movimentacao, Produto, TipoMovimentacao
from app.services import estoque_service, produto_service

DIAS_MAXIMO = 365
TOP_SAIDAS = 5
MAX_ALERTAS = 10
CENTAVO = Decimal("0.01")


def resumo(usuario_logado, dias: int = 30) -> dict:
    if not 1 <= dias <= DIAS_MAXIMO:
        raise RequisicaoInvalida(
            f"O período deve ter entre 1 e {DIAS_MAXIMO} dias.", campo="dias"
        )
    ate = datetime.now(timezone.utc).date()
    de = ate - timedelta(days=dias - 1)
    inicio = datetime.combine(de, time.min, tzinfo=timezone.utc)
    empresa_id = usuario_logado.empresa_id

    return {
        "periodo": {"de": de, "ate": ate, "dias": dias},
        "kpis": _kpis(empresa_id, inicio),
        "serie_diaria": _serie_diaria(empresa_id, inicio, de, dias),
        "valor_por_categoria": _valor_por_categoria(empresa_id),
        "top_saidas": _top_saidas(empresa_id, inicio),
        "alertas": produto_service.em_ruptura(usuario_logado, 1, MAX_ALERTAS)["itens"],
    }


def _valor_em_estoque():
    return Produto.saldo_atual * Produto.preco_custo


def _dinheiro(valor) -> float:
    return float(Decimal(str(valor or 0)).quantize(CENTAVO, rounding=ROUND_HALF_UP))


def _kpis(empresa_id: int, inicio: datetime) -> dict:
    valor, ativos, em_ruptura = (
        db.session.query(
            func.sum(_valor_em_estoque()),
            func.count(Produto.id),
            func.sum(case((estoque_service.condicao_ruptura(), 1), else_=0)),
        )
        .filter(Produto.empresa_id == empresa_id, Produto.ativo.is_(True))
        .one()
    )
    movimentacoes = (
        db.session.query(func.count(Movimentacao.id))
        .join(Produto, Movimentacao.produto_id == Produto.id)
        .filter(Produto.empresa_id == empresa_id, Movimentacao.criado_em >= inicio)
        .scalar()
    )
    return {
        "valor_estoque": _dinheiro(valor),
        "produtos_ativos": ativos,
        "em_ruptura": int(em_ruptura or 0),
        "movimentacoes": movimentacoes,
    }


def _dia_utc(dialeto: str):
    """Dia UTC do registro. No Postgres, date(timestamptz) usaria o fuso da sessão."""
    if dialeto == "postgresql":
        return func.date(func.timezone("UTC", Movimentacao.criado_em))
    return func.date(Movimentacao.criado_em)


def _serie_diaria(empresa_id: int, inicio: datetime, de, dias: int) -> list[dict]:
    dia = _dia_utc(db.engine.dialect.name)
    linhas = (
        db.session.query(
            dia,
            func.sum(case((Movimentacao.tipo == TipoMovimentacao.ENTRADA, Movimentacao.quantidade), else_=0)),
            func.sum(case((Movimentacao.tipo == TipoMovimentacao.SAIDA, Movimentacao.quantidade), else_=0)),
        )
        .join(Produto, Movimentacao.produto_id == Produto.id)
        .filter(Produto.empresa_id == empresa_id, Movimentacao.criado_em >= inicio)
        .group_by(dia)
        .all()
    )
    # date() devolve texto no SQLite e date no Postgres; str()[:10] iguala os dois.
    por_dia = {str(data)[:10]: (int(entradas or 0), int(saidas or 0))
               for data, entradas, saidas in linhas}
    serie = []
    for deslocamento in range(dias):
        data = (de + timedelta(days=deslocamento)).isoformat()
        entradas, saidas = por_dia.get(data, (0, 0))
        serie.append({"data": data, "entradas": entradas, "saidas": saidas})
    return serie


def _valor_por_categoria(empresa_id: int) -> list[dict]:
    total = func.sum(_valor_em_estoque())
    linhas = (
        db.session.query(Categoria.nome, total)
        .join(Produto, Produto.categoria_id == Categoria.id)
        .filter(Produto.empresa_id == empresa_id, Produto.ativo.is_(True))
        .group_by(Categoria.id, Categoria.nome)
        .order_by(total.desc(), Categoria.nome)
        .all()
    )
    return [{"categoria": nome, "valor": _dinheiro(valor)} for nome, valor in linhas]


def _top_saidas(empresa_id: int, inicio: datetime) -> list[dict]:
    total = func.sum(Movimentacao.quantidade)
    linhas = (
        db.session.query(Produto.id, Produto.nome, total)
        .join(Movimentacao, Movimentacao.produto_id == Produto.id)
        .filter(
            Produto.empresa_id == empresa_id,
            Movimentacao.tipo == TipoMovimentacao.SAIDA,
            Movimentacao.criado_em >= inicio,
        )
        .group_by(Produto.id, Produto.nome)
        .order_by(total.desc(), Produto.nome)
        .limit(TOP_SAIDAS)
        .all()
    )
    return [{"produto_id": pid, "nome": nome, "quantidade": int(qtd)} for pid, nome, qtd in linhas]
