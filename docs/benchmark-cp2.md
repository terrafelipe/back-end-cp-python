# Benchmark do CP2

`python scripts/benchmark.py`: SQLite temporário, 500 produtos, 20 mil movimentações,
20 repetições por rota, medido pelo test client do Flask (sem rede). Máquina: PC de casa
(Windows 11), Python 3.14.

## Antes (saldo derivado do histórico, commit 17b659c)

| rota | mediana (ms) | p95 (ms) |
|---|---|---|
| `/estoque/alertas` | 176.5 | 204.1 |
| `/produtos?em_ruptura=true` | 180.4 | 960.9 |
| `/produtos` | 40.1 | 131.1 |
| `/estoque/saldo` | 37.2 | 129.9 |
| `/dashboard/resumo` | não existe | — |

## Depois (saldo em cache, commit ca48634)

| rota | mediana (ms) | p95 (ms) |
|---|---|---|
| `/estoque/alertas` | 1.6 | 2.3 |
| `/produtos?em_ruptura=true` | 1.6 | 2.2 |
| `/produtos` | 2.4 | 3.5 |
| `/estoque/saldo` | 2.2 | 2.9 |
| `/dashboard/resumo` | 26.7 | 29.3 |

## Leitura

Alertas e o filtro de ruptura caíram de ~180 ms para ~1,6 ms (cerca de 100×): antes cada leitura
percorria as 20 mil movimentações em Python e paginava em memória; agora o filtro
`saldo_atual < estoque_minimo` e a paginação rodam no banco, apoiados no índice
`produto(empresa_id, ativo)`. O custo é uma escrita a mais (o cache) a cada movimentação.
O dashboard inteiro, que não existia, responde em ~27 ms numa só requisição.
