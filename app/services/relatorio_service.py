"""Relatório de reposição (RN-06 + consumo recente).

O sistema calcula todos os números: saldo, consumo, cobertura e quantidade
sugerida. A LLM, quando disponível, só reordena por urgência e escreve a
justificativa. Sem ela, o relatório sai pelas regras abaixo e diz isso no
campo `origem` (decisões D5 e D6 da SPEC-CP2).
"""

import logging
from datetime import datetime, timedelta, timezone

from flask import current_app
from sqlalchemy import func

from app.errors import NaoEncontrado
from app.extensions import db
from app.models import (
    Categoria, Movimentacao, OrigemRelatorio, Produto, RelatorioIA, TipoMovimentacao,
)
from app.services import estoque_service
from app.services.llm import cliente as cliente_llm
from app.services.llm import reposicao as prompt_reposicao
from app.services.paginacao import paginar

logger = logging.getLogger(__name__)

JANELA_CONSUMO_DIAS = 30
COBERTURA_ALERTA_DIAS = 15


def _dias_ate_acabar(saldo: int, consumo_30d: int) -> float | None:
    """Cobertura no ritmo dos últimos 30 dias. None = não houve saída."""
    if saldo <= 0:
        return 0.0
    if consumo_30d == 0:
        return None
    return round(saldo / (consumo_30d / JANELA_CONSUMO_DIAS), 1)


def _quantidade_sugerida(saldo: int, minimo: int, consumo_30d: int) -> int:
    """Leva o saldo a 2× o mínimo ou a 30 dias de consumo, o que for maior."""
    return max(max(minimo * 2, consumo_30d) - saldo, 1)


def _candidatos(empresa_id: int) -> list[dict]:
    """Produtos ativos em ruptura ou com até 15 dias de cobertura.

    Cada item leva só o que pode ir para a LLM (D7): nada de usuário,
    e-mail, CNPJ, fornecedor ou empresa.
    """
    inicio = datetime.now(timezone.utc) - timedelta(days=JANELA_CONSUMO_DIAS)
    saidas = (
        db.session.query(
            Movimentacao.produto_id, func.sum(Movimentacao.quantidade).label("total")
        )
        .filter(Movimentacao.tipo == TipoMovimentacao.SAIDA, Movimentacao.criado_em >= inicio)
        .group_by(Movimentacao.produto_id)
        .subquery()
    )
    linhas = (
        db.session.query(Produto, Categoria.nome, func.coalesce(saidas.c.total, 0))
        .join(Categoria, Produto.categoria_id == Categoria.id)
        .outerjoin(saidas, saidas.c.produto_id == Produto.id)
        .filter(Produto.empresa_id == empresa_id, Produto.ativo.is_(True))
        .order_by(Produto.sku)
        .all()
    )

    itens = []
    for produto, categoria, consumo in linhas:
        consumo = int(consumo)
        dias = _dias_ate_acabar(produto.saldo_atual, consumo)
        em_ruptura = estoque_service.em_ruptura(produto.estoque_minimo, produto.saldo_atual)
        if not em_ruptura and (dias is None or dias > COBERTURA_ALERTA_DIAS):
            continue
        itens.append({
            "sku": produto.sku,
            "nome": produto.nome,
            "categoria": categoria,
            "saldo": produto.saldo_atual,
            "estoque_minimo": produto.estoque_minimo,
            "consumo_30d": consumo,
            "custo_medio": float(produto.preco_custo or 0),
            "dias_ate_acabar": dias,
            "quantidade_sugerida": _quantidade_sugerida(
                produto.saldo_atual, produto.estoque_minimo, consumo
            ),
        })
    return itens


def _motivo(item: dict) -> str:
    if item["saldo"] < item["estoque_minimo"]:
        return f"Saldo {item['saldo']} abaixo do mínimo de {item['estoque_minimo']}."
    dias = str(item["dias_ate_acabar"]).replace(".", ",")
    return f"Estoque para cerca de {dias} dias no ritmo atual."


def _por_regras(itens: list[dict]) -> dict:
    ordenados = sorted(
        itens,
        key=lambda i: (i["dias_ate_acabar"] is None, i["dias_ate_acabar"] or 0, i["sku"]),
    )
    prioridades = [
        {"sku": i["sku"], "nome": i["nome"],
         "quantidade_sugerida": i["quantidade_sugerida"], "motivo": _motivo(i)}
        for i in ordenados
    ]
    if not prioridades:
        return {"resumo": "Nenhum produto precisa de reposição agora.", "prioridades": []}
    abaixo = sum(1 for i in itens if i["saldo"] < i["estoque_minimo"])
    resumo = f"{len(prioridades)} produto(s) precisam de reposição; {abaixo} já abaixo do mínimo."
    return {"resumo": resumo, "prioridades": prioridades}


def _pela_llm(itens: list[dict], regras: dict) -> dict | None:
    """Tenta a LLM; None em qualquer problema, e o relatório sai pelas regras.

    O `except Exception` é deliberado: um serviço externo fora do ar nunca
    pode virar erro 500 na tela.
    """
    chave = current_app.config.get("GROQ_API_KEY")
    if not itens or not chave:
        return None
    try:
        bruto = cliente_llm.completar_json(
            prompt_reposicao.montar_mensagens(itens),
            modelo=current_app.config["GROQ_MODEL"],
            chave=chave,
            timeout_s=current_app.config["LLM_TIMEOUT_S"],
        )
    except Exception:  # noqa: BLE001
        logger.warning("LLM indisponível; relatório gerado pelas regras.", exc_info=True)
        return None
    validado = prompt_reposicao.validar_resposta(bruto, regras)
    if validado is None:
        logger.warning("Resposta da LLM fora do formato; relatório gerado pelas regras.")
    return validado


def gerar_reposicao(usuario_logado) -> RelatorioIA:
    itens = _candidatos(usuario_logado.empresa_id)
    regras = _por_regras(itens)
    pela_llm = _pela_llm(itens, regras)

    relatorio = RelatorioIA(
        empresa_id=usuario_logado.empresa_id,
        usuario_id=usuario_logado.id,
        origem=OrigemRelatorio.LLM if pela_llm else OrigemRelatorio.REGRAS,
        modelo=current_app.config["GROQ_MODEL"] if pela_llm else None,
        entrada={"produtos": itens},
        resultado=pela_llm or regras,
    )
    db.session.add(relatorio)
    db.session.commit()
    return relatorio


def _da_empresa(usuario_logado):
    return RelatorioIA.query.filter(
        RelatorioIA.empresa_id == usuario_logado.empresa_id
    ).order_by(RelatorioIA.criado_em.desc(), RelatorioIA.id.desc())


def ultimo(usuario_logado) -> RelatorioIA:
    relatorio = _da_empresa(usuario_logado).first()
    if relatorio is None:
        raise NaoEncontrado("Nenhum relatório de reposição foi gerado ainda.")
    return relatorio


def listar(usuario_logado, pagina: int, por_pagina: int) -> dict:
    return paginar(_da_empresa(usuario_logado), pagina, por_pagina)
