# Gestor de Estoque (API): backend Flask do checkpoint de Python da FIAP, grupo de 5 alunos

@docs/GRUPO.md

## Por quê / escopo
- API REST de estoque para pequeno comércio: produtos, categorias, fornecedores, usuários,
  movimentações (entrada/saída/ajuste), saldo, custo médio e alertas de ruptura. Multi-tenant.
- **Fora de escopo:** nota fiscal, marketplaces, multi-armazém, lote/número de série.
- **Entrega atual: CP2 (06/10)** — `docs/SPEC-CP2.md`. Fora do CP2: deploy, Docker, chatbot livre.
- Front-end em repo separado (`../frontend`, `front-end-cp-python`).

## Stack e estrutura
- Python 3.12+ (o PC roda 3.14), Flask + flask-restx (Swagger em `/swagger`), SQLAlchemy +
  Flask-Migrate (Alembic), SQLite (`estoque.db`), JWT + bcrypt, flask-cors. Sem deploy ainda.
- `app/controllers/` só HTTP · `app/services/` toda regra de negócio · `app/schemas/` entrada/saída
  do restx · `app/models/` persistência · `app/errors.py` envelope de erro · `app/security.py` auth.

## Comandos
- Setup: `python -m venv .venv; .\.venv\Scripts\python.exe -m pip install -r requirements.txt`
- Dados demo: `.\.venv\Scripts\python.exe seed.py` (`--recriar` apaga e gera de novo)
- Rodar: `.\.venv\Scripts\python.exe app.py` → http://127.0.0.1:5000/swagger
- Testes: `.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt` (uma vez) e `.\.venv\Scripts\python.exe -m pytest -q`
- Migration nova: `.\.venv\Scripts\flask.exe db migrate -m "..."` e revisar o arquivo gerado

## Regras do projeto
- Regra de negócio só em `services/`; controller nunca decide. Violação = exceção de domínio com
  código `RN-xx` → HTTP 422 no envelope `{"erro": {"codigo", "mensagem", "campo"}}`.
- Nunca criar coluna de saldo: é derivado das movimentações. Movimentação é imutável (RN-04).
- `AJUSTE` define o saldo (contagem), não soma. Quantidade sempre positiva (RN-03).
- Recurso de outra empresa responde 404, nunca 403 (RN-08). `empresa_id` vem do token, nunca do cliente.
- Schemas de saída separados dos de entrada; senha nunca aparece em resposta.
- Só tipos genéricos do SQLAlchemy (Postgres tem que funcionar trocando `DATABASE_URL`).
- Lista paginada sempre no envelope `{itens, pagina, por_pagina, total, total_paginas}`.
- JSON em `snake_case`, código e mensagens em português.
- Mudou regra, endpoint ou schema: atualizar o README (RN, endpoints, roteiro) no mesmo commit.
- Commits pequenos, assunto sem acento; push só com ok do Felipe (repo do grupo).

## Como trabalhar aqui
- Retomar o trabalho: `/briefing` (lê a ficha `projetos/cp-python.md` do AIOS e as Issues `aios`).
- Plano do back aprovado: `docs/superpowers/plans/2026-09-25-cp2-backend.md`. Uma task por vez,
  na ordem (testes antes do código); os desvios da SPEC aprovados estão no fim do plano.
- Tarefa que mexe nas duas pontas: sessão aqui com `/add-dir ../frontend`.
- Revisão cruzada `/revisar` (Codex) depois da Task 6 e no fim do plano.
- Fechou tarefa: atualizar o Status do card no Notion "Tarefas do CP2" (com ok do Felipe) e a ficha.

## Armadilhas
- Booleano em query string: usar `argumento_booleano` (`inputs.boolean`), nunca `type=bool`.
- `ERROR_INCLUDE_MESSAGE=False` e `PROPAGATE_EXCEPTIONS=False` mantêm o envelope único e sem
  traceback; não remover.
- SQLite precisa de `render_as_batch=True` nas migrations e do PRAGMA de FK (em `extensions.py`).
- `.claude/` está no `.gitignore`: configuração do Claude aqui não viaja pelo git.
- `.env.example` é UTF-8; no PowerShell 5.1 ler com `-Encoding UTF8`.

## Documentação
- Estado, contrato e pontos de atenção: `contexto.md` · Testar: `docs/COMO_TESTAR.md`
- Regras RN-01..RN-10, endpoints e roteiro de validação: `README.md`
