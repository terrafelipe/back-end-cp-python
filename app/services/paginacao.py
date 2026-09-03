"""Envelope único de listagem paginada.

Todo recurso paginado da API responde neste formato. Centralizar aqui é o
que garante que produtos, movimentações e usuários não divirjam.
"""

from app.errors import RequisicaoInvalida

POR_PAGINA_PADRAO = 20
POR_PAGINA_MAXIMO = 100


def _validar(pagina: int, por_pagina: int) -> None:
    if pagina < 1:
        raise RequisicaoInvalida(
            "A página deve ser maior ou igual a 1.", campo="pagina"
        )
    if not 1 <= por_pagina <= POR_PAGINA_MAXIMO:
        raise RequisicaoInvalida(
            f"O tamanho da página deve estar entre 1 e {POR_PAGINA_MAXIMO}.",
            campo="por_pagina",
        )


def paginar(query, pagina: int = 1, por_pagina: int = POR_PAGINA_PADRAO) -> dict:
    """Aplica a paginação e devolve o envelope descrito no README."""
    _validar(pagina, por_pagina)

    # error_out=False: página além do fim devolve lista vazia, não 404.
    resultado = query.paginate(page=pagina, per_page=por_pagina, error_out=False)
    return {
        "itens": resultado.items,
        "pagina": resultado.page,
        "por_pagina": resultado.per_page,
        "total": resultado.total,
        "total_paginas": resultado.pages,
    }


def paginar_lista(itens: list, pagina: int, por_pagina: int) -> dict:
    """Mesmo envelope, para listas já materializadas em memória.

    Necessário quando o filtro depende do saldo: como o saldo é derivado do
    histórico e não existe como coluna, o banco não consegue filtrar por ele.
    """
    _validar(pagina, por_pagina)
    inicio = (pagina - 1) * por_pagina
    total = len(itens)
    return {
        "itens": itens[inicio : inicio + por_pagina],
        "pagina": pagina,
        "por_pagina": por_pagina,
        "total": total,
        "total_paginas": (total + por_pagina - 1) // por_pagina,
    }
