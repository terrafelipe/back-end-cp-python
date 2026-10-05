# SPEC — Checkpoint 2: Aplicação, Dashboard, Otimização e IA

> Criada em 25/09/2026 a partir do enunciado (`docs/CHECKPOINT 2.pdf`) e da entrevista com o Felipe.
> **Entrega: 06/10/2026.** Contrato entre os repos: `docs/GRUPO.md`.

## 1. Pedido (barema, 10 pontos)

| Critério | Pontos | Onde |
|---|---|---|
| Evolução e qualidade do backend | 0,5 | back |
| Frontend e integração com a API | 2,0 | front |
| Dashboard e visualização | 2,0 | back + front |
| Otimização da API | 0,5 | back |
| Modelagem, normalização e evolução do banco | 1,0 | back |
| Documentação e Swagger | 0,5 | back + front |
| Testes iniciais | 1,0 | back + front |
| Aplicação e integração da LLM | 1,0 | back + front |
| Organização ágil (Notion) | 0,5 | Notion |
| Apresentação e domínio técnico | 1,0 | fora desta SPEC (decidir depois) |

## 2. Já existe (conferido no código em 25/09/2026)

- API Flask + flask-restx com 20 rotas, RN-01..RN-10, envelope de erro único, JWT, papéis
  ADMIN/OPERADOR, multi-tenant por `empresa_id`, paginação e filtros em produtos e movimentações.
- Banco: 6 tabelas, FKs, uniques por empresa, checks, 1 migration; índices só em
  `movimentacao.produto_id`, `movimentacao.criado_em`, `produto.sku`, `usuario.email`.
- Seed com 8 produtos (3 em ruptura). README completo. CORS aberto (`*`).
- **Não existe:** testes, front (repo vazio), dashboard, LLM.

## 3. Decisões

| # | Decisão | Motivo |
|---|---|---|
| D1 | Felipe + Claude implementam tudo; branch `cp2` em cada repo; merge e push só com ok | 11 dias; coordenação de 5 pessoas custa mais que ajuda |
| D2 | Ordem: back (dias 1–3) → front (4–8) → E2E, docs, Notion (9–10) → ensaio (11) | front consome o contrato pronto |
| D3 | Coluna `produto.saldo_atual` como cache, atualizada na mesma transação da movimentação | previsto no README do CP1; ruptura e paginação passam para o banco |
| D4 | Um endpoint para o dashboard: `GET /dashboard/resumo?dias=30` | 1 requisição em vez de ~6 |
| D5 | LLM = relatório de reposição via Groq, gerado por botão e salvo em `relatorio_ia` | ligada a RN-06/RN-07; histórico evita chamadas repetidas |
| D6 | Backend calcula todos os números; a LLM só prioriza e justifica | LLM não inventa número |
| D7 | Para a Groq vão só: nome, SKU, categoria, saldo, mínimo, consumo 30 d, custo médio, dias até acabar | nenhum dado de usuário, e-mail, CNPJ, fornecedor ou empresa |
| D8 | Front: React + Vite + TypeScript + Tailwind + shadcn/ui + Recharts | ~7 telas com formulários, tabelas e toasts |
| D9 | Token no `localStorage`; logout automático no 401 | escolha do Felipe (conveniência na demo); mitigado por React sem `innerHTML` |
| D10 | Desktop primeiro, celular usável (menu em gaveta, tabelas com rolagem) | demo no projetor |
| D11 | Testes: pytest no back (LLM simulada) + 3–5 fluxos Playwright (pytest) no front | "testes executáveis demonstrados" |
| D12 | Otimização provada por script de benchmark antes/depois, números no README | "explicar as otimizações" |
| D13 | Notion atualizado pelo Claude via MCP, com ok do Felipe | 0,5 ponto |

## 4. Fora de escopo do CP2

Deploy, Docker/containerização, apresentação/slides (decidir depois), nota fiscal, marketplaces,
multi-armazém, lote/número de série, chatbot livre, streaming da resposta da LLM, i18n (só pt-BR).

## 5. Falta — backend (`back-end-cp-python`)

**B1. Testes (primeiro, para proteger o CP1)** — `tests/` com pytest, SQLite em memória, fixtures
de app, cliente, empresa demo e tokens ADMIN/OPERADOR; `pytest` em `requirements-dev.txt`.

**B2. Banco revisado** — migration nova:
- `produto.saldo_atual` (inteiro, não nulo, padrão 0, `CHECK >= 0`), preenchida pelo histórico
  existente na própria migration; atualizada só em `movimentacao_service.registrar`.
- Índices: `produto(empresa_id, ativo)`, `produto.categoria_id`, `produto.fornecedor_id`,
  `categoria.empresa_id`, `fornecedor.empresa_id`, `usuario.empresa_id`, `movimentacao.usuario_id`.
- Tabela `relatorio_ia`: `id, empresa_id FK, usuario_id FK, origem ('LLM'|'REGRAS'), modelo,
  entrada JSON, resultado JSON, criado_em`; índice `(empresa_id, criado_em)`.
- README: seção "Revisão do banco (CP2)" com a justificativa da desnormalização e dos índices.

**B3. Otimização**
- `/produtos?em_ruptura=`, `/estoque/alertas` e `/estoque/saldo` filtram e paginam no banco usando
  `saldo_atual`, sem ler o histórico.
- `GET /dashboard/resumo?dias=30` (formato em `docs/GRUPO.md`), com agregações em SQL.
- `scripts/benchmark.py`: popula banco temporário (500 produtos, 20 mil movimentações), mede
  alertas, produtos e dashboard; roda antes e depois das mudanças; resultado no README.

**B4. Endurecimento**
- `FLASK_DEBUG=0` + `SECRET_KEY` ou `JWT_SECRET_KEY` ausente/de dev → a app não sobe (erro claro).
- Login: 5 falhas por e-mail+IP em 15 min → 429 `HTTP-429` no envelope padrão (memória do processo).
- `CORS_ORIGINS` padrão `http://localhost:5173,http://127.0.0.1:5173`.
- Validação de formato de e-mail e dígitos verificadores de CNPJ (empresa e fornecedor) → 400/422.

**B5. LLM** — `app/services/llm/` (cliente Groq atrás de uma função, fácil de trocar):
- `POST /relatorios/reposicao` monta a entrada (D7) com produtos em ruptura ou com ≤ 15 dias de
  cobertura, chama a Groq pedindo JSON (`prioridades[{sku, quantidade_sugerida, motivo}]`, `resumo`),
  valida a saída e salva. Sem `GROQ_API_KEY`, timeout ou JSON inválido → relatório `origem=REGRAS`
  (ordem por dias até acabar, quantidade = mínimo × 2 − saldo), nunca erro 500.
- `GET /relatorios/reposicao/ultimo` e `GET /relatorios/reposicao` (paginado).
- Nomes de produto vão como dado dentro do JSON, com instrução explícita de ignorar ordens contidas neles.
- Variáveis novas: `GROQ_API_KEY`, `GROQ_MODEL` (padrão `openai/gpt-oss-120b`; o `llama-3.3-70b-versatile` original saiu da Groq em 2026-10-05), `LLM_TIMEOUT_S`.

**B6. Seed** — `seed.py` gera ~60 dias de movimentações com datas passadas (entradas semanais,
saídas diárias), mantendo 3 produtos em ruptura.

**B7. Docs** — README: arquitetura com o front, dashboard, LLM (modelo, finalidade, dados enviados,
resposta, uso, limitações, segurança), testes, benchmark, variáveis novas, novos endpoints; Swagger
com modelos e exemplos das rotas novas; `docs/COMO_TESTAR.md` e `contexto.md` atualizados.

## 6. Falta — frontend (`front-end-cp-python`)

- **F1. Esqueleto:** Vite + React + TS, Tailwind, shadcn/ui, React Router, Recharts; `.env.example`
  com `VITE_API_URL=http://127.0.0.1:5000`; cliente HTTP único que injeta o token, trata o envelope
  de erro e desloga no 401; `CLAUDE.md`, README com integrantes e como rodar.
- **F2. Autenticação:** login, cadastro de empresa, rota protegida, menu conforme o papel.
- **F3. Dashboard (home):** 4 KPIs, entradas × saídas por dia, valor por categoria, top 5 saídas,
  tabela de alertas, seletor de período (7/30/90 dias), card do relatório com "Gerar análise",
  estado de carregamento e rótulo "gerado por IA" ou "gerado por regras".
- **F4. Produtos:** lista paginada com busca, categoria, ruptura; criar/editar em diálogo; inativar
  com confirmação; histórico do produto. Preço de venda só editável por ADMIN.
- **F5. Movimentações:** formulário entrada/saída/ajuste (custo só em entrada), extrato com filtros.
- **F6. Categorias, fornecedores, usuários:** CRUDs; fornecedores e usuários só para ADMIN.
- **F7. Feedback:** toast de sucesso em toda operação; erro mostra `erro.mensagem` e destaca `erro.campo`;
  estados vazio, carregando e erro em toda lista.
- **F8. E2E:** `e2e/` com pytest-playwright: login, dashboard carrega números do seed, criar produto,
  saída acima do saldo mostra a mensagem RN-02, operador não vê menu de usuários; 1 viewport de celular.

## 7. Critérios de pronto (testáveis)

1. `pytest -q` no back passa com ≥ 35 testes, cobrindo RN-01..RN-10, 401/403/404 entre empresas,
   429 no login, cache de saldo igual ao derivado após entrada, saída e ajuste, dashboard e LLM
   (sucesso, sem chave, timeout, JSON inválido) sem acesso à rede.
2. Roteiro de 11 passos do README do CP1 continua passando.
3. `python app.py` com `FLASK_DEBUG=0` e sem chaves falha com mensagem clara.
4. `/dashboard/resumo` responde em 1 requisição tudo o que a tela usa; o front não faz outra chamada
   para montar o dashboard (exceto o último relatório).
5. Benchmark mostra redução em `/estoque/alertas` e está registrado no README.
6. Relatório gerado sem `GROQ_API_KEY` retorna `origem=REGRAS`; com chave retorna `origem=LLM`.
7. `npm run build` e `npm run lint` passam no front; os fluxos E2E passam com back e front locais.
8. Nenhuma tela usa `dangerouslySetInnerHTML`; nenhum segredo commitado nos dois repos.
9. README dos dois repos e Swagger descrevem tudo o que foi entregue; Notion com cards do CP2.

## 8. Riscos

| Risco | Mitigação |
|---|---|
| Cache de saldo divergir do histórico | só `registrar` escreve; teste compara com o derivado; migration faz o backfill |
| Groq fora do ar ou cota esgotada na demo | relatório por regras + último relatório salvo aparece sem nova chamada |
| Prompt injection pelo nome do produto | dado vai em JSON, saída validada, a LLM não executa nada |
| Token no `localStorage` exposto a XSS | nenhum HTML cru; dependências fixas; logout no 401 |
| Front atrasar (4 dos 10 pontos) | back fechado até o dia 3; shadcn para não construir componente do zero |
| Migration no SQLite (ALTER limitado) | modo batch já ativo; testar `upgrade` num banco com dados do seed |
