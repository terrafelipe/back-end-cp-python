# Contexto do Projeto — Gestor de Estoque (CP2)

> Atualizado em 05/10/2026. Documento de contexto: propósito, arquitetura, contrato de dados,
> testes e pontos de atenção. Regras de negócio (RN-01 a RN-10), endpoints, revisão do banco,
> otimização e relatório com IA em detalhe ficam no `README.md`. Entrega do CP2: 06/10/2026
> (`docs/SPEC-CP2.md`).

## 1. Visão geral

API REST de controle de estoque para pequeno comércio (FIAP, Tecnologia em IA, grupo de 5).
Cadastra produtos, categorias, fornecedores e usuários; registra entradas, saídas e ajustes; calcula
saldo, custo médio ponderado e alertas de ruptura. Multi-tenant por `empresa_id`. No CP2 ganhou
dashboard numa requisição, relatório de reposição com IA, cache de saldo, testes automatizados e
um front-end web.

- Repo: `github.com/terrafelipe/back-end-cp-python` (trabalho do CP2 na branch `cp2`; a `main`
  está no CP1 até o merge da entrega). Irmão: `front-end-cp-python` (React, seção 7).
- Sem deploy: roda local com SQLite em `estoque.db`. Gestão no Notion (link no README).
- Serviço externo: Groq (LLM do relatório), opcional; sem chave o relatório sai pelas regras.
- Fora de escopo do produto: nota fiscal, marketplaces, multi-armazém, lote ou número de série.
  Fora do CP2: deploy, Docker e chatbot livre.

## 2. Arquitetura

```
front React (:5173) --HTTP+JWT--> controllers (flask-restx, :5000)
        --> services (regra de negócio, códigos RN-xx) --> models (SQLAlchemy) --> SQLite/Postgres
                    \--> relatorio_service --> llm/cliente.py --> Groq (opcional, com fallback)
```

- Controllers só traduzem HTTP; toda regra está em `app/services/`.
- **Saldo em cache** (CP2): `produto.saldo_atual`, escrito só por `movimentacao_service.registrar`
  na mesma transação da movimentação, com o produto travado antes de ler o saldo. Os testes
  comparam o cache com o saldo derivado do histórico. No CP1 o saldo era só derivado.
- `AJUSTE` define o saldo (contagem de inventário), não soma.
- `usuario_atual()` relê o usuário do banco a cada requisição: desativar vale na hora.
- Erro sempre no envelope `{"erro": {"codigo", "mensagem", "campo"}}` (`app/errors.py`).
- A LLM só ordena e justifica: as quantidades sugeridas são sempre calculadas pelo sistema.

## 3. Estrutura de diretórios

```
app.py              ponto de entrada; aplica migrations e sobe o servidor
seed.py             empresa demo + admin/operador + 60 dias de histórico (3 produtos em ruptura)
app/__init__.py     application factory, CORS, registro dos namespaces
app/config.py       configuração por env var, tudo com padrão de desenvolvimento
app/errors.py       exceções de domínio e tratadores (nenhum stack trace ao cliente)
app/security.py     bcrypt, usuario_atual(), decorator somente_admin
app/controllers/    camada HTTP (1 namespace por recurso; dashboard e relatorios no CP2)
app/services/       regras de negócio, paginação, permissões; dashboard_service, relatorio_service
app/services/llm/   cliente.py (Groq, atrás de uma função) e reposicao.py (prompt e validação)
app/schemas/        modelos de entrada/saída do flask-restx (senha nunca sai)
app/models/         Empresa, Usuario, Categoria, Fornecedor, Produto, Movimentacao, RelatorioIA
migrations/         Alembic; 2 revisões (1abc8de16adf estrutura inicial; 2c9f4e1a7b3d cache,
                    índices e relatorio_ia)
scripts/benchmark.py  mede as leituras de estoque (resultado em docs/benchmark-cp2.md)
tests/              suíte pytest (seção 10)
docs/               SPEC-CP2, GRUPO.md (contrato com o front), COMO_TESTAR, benchmark, plano
```

## 5. Banco de dados

SQLite por padrão (`sqlite:///estoque.db`); Postgres trocando só `DATABASE_URL` (driver
`psycopg[binary]` já no requirements). Migrations em modo batch (`render_as_batch=True`) e aplicadas
sozinhas ao subir (`AUTO_MIGRATE=1`). FK ligada no SQLite por `PRAGMA` em cada conexão.

Revisão do CP2 (migration `2c9f4e1a7b3d`): coluna `produto.saldo_atual` com
`CHECK (saldo_atual >= 0)` e backfill a partir do histórico; índices nas FKs e em
`produto(empresa_id, ativo)`; tabela `relatorio_ia` (origem `LLM`/`REGRAS`, modelo, entrada e
resultado em JSON). O resto segue na 3FN. Diagrama ER e decisões: README, "Modelo de dados".

## 6. API / backend

24 regras de URL no `url_map` (contadas em 05/10/2026), incluindo `/`, `/health`, `/swagger`,
`/swagger.json` e `/swaggerui/...`. Novas no CP2: `GET /dashboard/resumo?dias=30`,
`POST /relatorios/reposicao` e `GET /relatorios/reposicao/ultimo` (404 se nunca gerado).
Tabela completa no README, seção "Endpoints". Perfis: `ADMIN` (tudo) e `OPERADOR` (movimenta e
consulta; não exclui produto nem cria fornecedor, usuário ou preço de venda). Códigos: 422 = regra
de negócio violada; 405 = tentar editar movimentação (RN-04); 404 (nunca 403) para recurso de outra empresa.

- **Dashboard:** uma requisição com KPIs, série diária de entradas/saídas, valor por categoria,
  top 5 saídas e alertas; somas em SQL (`SUM`/`COUNT`/`GROUP BY`); dia da série contado em UTC.
- **Relatório de reposição:** envia à LLM só produtos ativos em ruptura ou com até 15 dias de
  cobertura (sem dado de usuário, CNPJ ou fornecedor); valida a resposta (SKU inventado é
  descartado). Sem chave, com timeout (`LLM_TIMEOUT_S`) ou resposta inválida, sai pelas regras.
  Nunca 500.

## 7. Frontend

Repo `front-end-cp-python` (`../frontend`, branch `cp2`): React 19 + Vite 8 + TypeScript 6,
Tailwind 4, React Router 7 e Recharts 3. Telas em `src/pages/`: Login, Cadastro, Dashboard (com
o botão "Gerar análise" do relatório), Produtos, ProdutoHistorico, Movimentações, Categorias,
Fornecedores e Usuários. Um cliente HTTP único em `src/api/` lê `VITE_API_URL` (padrão
`http://127.0.0.1:5000`), injeta o token e desloga no 401. O menu esconde o que o papel não pode,
mas quem decide é sempre o back. Testes: Vitest e 6 fluxos E2E com Playwright (`e2e/test_fluxos.py`).

## 8. Segurança (resumo)

Senha com bcrypt, JWT com validade de 8 h, papel checado no servidor, isolamento por empresa vindo
do token. Chaves têm padrão de desenvolvimento em `config.py`: em qualquer ambiente público,
`SECRET_KEY` e `JWT_SECRET_KEY` precisam vir do ambiente. `.env` está no `.gitignore`; a
`GROQ_API_KEY` mora só nele. Nome de produto vai à LLM como dado dentro de JSON, com instrução de
ignorar ordens (prompt injection), e a saída é validada. CORS restrito ao front e limite de
tentativas de login são as Tasks 7–8 do plano (Issues #4 e #5); o estado atual de `CORS_ORIGINS`
está em `app/config.py` e na tabela de variáveis do README.

## 10. Testes

pytest, **88 testes** (`pytest --collect-only -q` em 05/10/2026). SQLite em memória recriado a cada
teste; nenhum teste acessa a rede (a Groq é simulada).

| Arquivo | Testes | Cobre |
|---|---|---|
| `test_auth_usuarios.py` | 13 | login, registro, papéis, isolamento entre empresas |
| `test_catalogo_estoque.py` | 22 | RN-01 a RN-10 em produtos, categorias, fornecedores e movimentações |
| `test_relatorio_llm.py` | 12 | caminho pela LLM: sucesso, sem chave, timeout, JSON inválido, SKU inventado, injeção |
| `test_dashboard.py` | 9 | formato do contrato, isolamento, período, top 5, dia em UTC |
| `test_relatorio_regras.py` | 9 | relatório por regras e endpoints |
| `test_leituras_otimizadas.py` | 7 | alertas, ruptura e paginação pelo cache |
| `test_cliente_groq.py` | 6 | cliente HTTP da Groq e erros |
| `test_cache_saldo.py` | 4 | cache igual ao saldo derivado após entrada, saída e ajuste |
| `test_seed.py` | 2 | seed determinístico com 3 rupturas |
| `test_benchmark.py`, `test_concorrencia.py`, `test_migracao.py`, `test_roteiro_cp1.py` | 1 cada | script de benchmark; duas saídas simultâneas (só uma passa); backfill da migration; roteiro do README automatizado |

Benchmark (`docs/benchmark-cp2.md`): `/estoque/alertas` caiu de 176,5 ms para 1,6 ms de mediana;
`/dashboard/resumo` responde em 26,7 ms.

## 11. Como rodar

```powershell
cd C:\dev\cp-python\backend
python -m venv .venv; .\.venv\Scripts\python.exe -m pip install -r requirements.txt -r requirements-dev.txt
.\.venv\Scripts\python.exe seed.py      # dados demo (--recriar apaga e gera de novo)
.\.venv\Scripts\python.exe app.py       # http://127.0.0.1:5000/swagger
.\.venv\Scripts\python.exe -m pytest -q
cd ..\frontend; npm install; npm run dev   # http://localhost:5173
```

Para o relatório sair pela IA, copiar `.env.example` para `.env` e preencher `GROQ_API_KEY`.

## 12. Contrato de dados (o que o front consome)

Fonte da verdade: `docs/GRUPO.md` (e o Swagger em `/swagger`).

| Elemento | Fonte da verdade |
|---|---|
| Login | `POST /auth/login` `{email, senha}` → `{access_token, usuario}` |
| Autenticação | cabeçalho `Authorization: Bearer <token>` em toda rota exceto register/login |
| Listas | envelope `{itens, pagina, por_pagina, total, total_paginas}`; `?pagina=&por_pagina=` |
| Produto | campos em `app/schemas/produto.py`; `saldo` e `em_ruptura` calculados |
| Movimentação | `tipo` ∈ `ENTRADA`, `SAIDA`, `AJUSTE`; `quantidade` sempre > 0 |
| Dashboard | `{periodo, kpis, serie_diaria, valor_por_categoria, top_saidas, alertas}` |
| Relatório | `{id, origem, modelo, criado_em, resultado: {resumo, prioridades}}` |
| Erro | `{"erro": {"codigo", "mensagem", "campo"}}`; mostrar `mensagem` ao usuário |

Regra: mudou um schema aqui, atualizar o front e o `docs/GRUPO.md` no mesmo dia.

## 13. Credenciais de teste (criadas pelo `seed.py`)

| Email | Senha | Perfil |
|---|---|---|
| `admin@demo.com` | `admin123` | ADMIN |
| `operador@demo.com` | `operador123` | OPERADOR |

## 14. Pontos de atenção

- `type=bool` em query string liga o filtro com `?x=false`: usar `inputs.boolean` (`argumento_booleano`).
- Com `FLASK_DEBUG=1` o Flask mostraria o traceback; `PROPAGATE_EXCEPTIONS=False` impede.
- flask-restx injeta `message` nos erros; `ERROR_INCLUDE_MESSAGE=False` mantém o envelope único.
- Acentos saíam escapados: `RESTX_JSON={"ensure_ascii": False}` e `app.json.ensure_ascii=False`.
- `.env.example` está em UTF-8; lido pelo PowerShell 5.1 sem `-Encoding UTF8` aparece com mojibake.
- O `llama-3.3-70b-versatile` saiu da Groq (404 `model_not_found`) e o relatório caía calado nas
  regras; padrão trocado para `openai/gpt-oss-120b`. Um `.env` antigo com `GROQ_MODEL` vence o padrão.
- Sem `User-Agent` próprio o urllib é recusado (403) pelo Cloudflare na frente da Groq.
- Duas saídas simultâneas furavam a RN-02: o produto é travado antes de ler o saldo (`610236e`).

## 15. Stack

Backend: Python 3.12+ (testado em 3.14), Flask 3.1, flask-restx 1.3, Flask-SQLAlchemy 3.1,
Flask-Migrate 4.1, flask-jwt-extended 4.7, bcrypt 5, flask-cors 6. Banco: SQLite (Postgres opcional).
IA: Groq `openai/gpt-oss-120b` via HTTP (urllib), com fallback por regras. Testes: pytest (back),
Vitest e Playwright (front). Frontend: React 19, Vite 8, TypeScript 6, Tailwind 4, Recharts 3.
Deploy: fora do CP2.
