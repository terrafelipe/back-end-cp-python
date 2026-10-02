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

## Depois

(preenchido na Task 13)
