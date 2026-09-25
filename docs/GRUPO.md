# Grupo de repos — Gestor de Estoque (CP Python)

| Pasta local | Repo | O que é |
|---|---|---|
| `C:\dev\cp-python\backend` | `terrafelipe/back-end-cp-python` | API Flask + SQLite (repo principal: SPEC, contrato) |
| `C:\dev\cp-python\frontend` | `terrafelipe/front-end-cp-python` | React + Vite + TypeScript |

**Regra:** commit e push em cada repo separadamente; mudou o contrato abaixo, atualizar este
arquivo e o front no mesmo dia. SPEC da entrega atual: `docs/SPEC-CP2.md`.

## Clonar e rodar juntos

```powershell
cd C:\dev\cp-python
git clone https://github.com/terrafelipe/back-end-cp-python.git backend
git clone https://github.com/terrafelipe/front-end-cp-python.git frontend
cd backend; python -m venv .venv; .\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe seed.py; .\.venv\Scripts\python.exe app.py     # :5000
cd ..\frontend; npm install; npm run dev                                   # :5173
```

## Contrato

- **URL da API:** `VITE_API_URL` no front (padrão `http://127.0.0.1:5000`).
- **CORS:** `CORS_ORIGINS` no back aceita `http://localhost:5173` e `http://127.0.0.1:5173`.
- **Auth:** `POST /auth/login {email, senha}` → `{access_token, usuario}`; demais rotas com
  `Authorization: Bearer <token>`; 401 = deslogar; 429 = muitas tentativas.
- **Erro:** `{"erro": {"codigo", "mensagem", "campo"}}`; mostrar `mensagem`, destacar `campo`.
- **Lista:** `{itens, pagina, por_pagina, total, total_paginas}`; query `pagina`, `por_pagina`.
- **Produto:** inclui `saldo` e `em_ruptura` (calculados); `preco_venda` só ADMIN altera.
- **Dashboard:** `GET /dashboard/resumo?dias=30` →
  `{periodo: {de, ate, dias}, kpis: {valor_estoque, produtos_ativos, em_ruptura, movimentacoes},
  serie_diaria: [{data, entradas, saidas}], valor_por_categoria: [{categoria, valor}],
  top_saidas: [{produto_id, nome, quantidade}], alertas: [Produto]}`.
- **Relatório IA:** `POST /relatorios/reposicao` → `{id, origem: "LLM"|"REGRAS", modelo, criado_em,
  resultado: {resumo, prioridades: [{sku, nome, quantidade_sugerida, motivo}]}}`;
  `GET /relatorios/reposicao/ultimo` (404 se nunca gerado).
- **Papéis:** OPERADOR não vê usuários nem fornecedores (escrita) e não exclui produto; o back
  sempre revalida (o menu do front é só conveniência).

Formatos de dashboard e relatório são o alvo do CP2; o Swagger (`/swagger`) é a fonte final.
