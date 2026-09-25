# Contexto do Projeto — Gestor de Estoque (CP1 entregue → CP2)

> Atualizado em 25/09/2026. Documento de contexto: propósito, arquitetura, contrato de dados,
> testes e pontos de atenção. Regras de negócio (RN-01 a RN-10), endpoints e roteiro de
> validação completos ficam no `README.md`, que foi conferido com o código nesta data.

## 1. Visão geral

API REST de controle de estoque para pequeno comércio (FIAP, Tecnologia em IA, grupo de 5).
Cadastra produtos, categorias, fornecedores e usuários; registra entradas, saídas e ajustes; calcula
saldo, custo médio ponderado e alertas de ruptura. Multi-tenant por `empresa_id`.

- Repo: `github.com/terrafelipe/back-end-cp-python` (`main`). Irmão: `front-end-cp-python` (vazio).
- Sem deploy: roda local com SQLite em `estoque.db`. Gestão no Notion (link no README).
- Fora de escopo do produto: nota fiscal, marketplaces, multi-armazém, lote ou número de série.

## 2. Arquitetura

```
cliente (Swagger hoje; front no CP2) --HTTP+JWT--> controllers (flask-restx)
        --> services (regra de negócio, códigos RN-xx) --> models (SQLAlchemy) --> SQLite/Postgres
```

- Controllers só traduzem HTTP; toda regra está em `app/services/`.
- O saldo **não é coluna**: é derivado das movimentações (`estoque_service.saldos`).
- `AJUSTE` define o saldo (contagem de inventário), não soma.
- `usuario_atual()` relê o usuário do banco a cada requisição: desativar vale na hora.
- Erro sempre no envelope `{"erro": {"codigo", "mensagem", "campo"}}` (`app/errors.py`).

## 3. Estrutura de diretórios

```
app.py            ponto de entrada; aplica migrations e sobe o servidor
seed.py           empresa demo + admin/operador + produtos (3 em ruptura)
app/__init__.py   application factory, CORS, registro dos namespaces
app/config.py     configuração por env var, tudo com padrão de desenvolvimento
app/errors.py     exceções de domínio e tratadores (nenhum stack trace ao cliente)
app/security.py   bcrypt, usuario_atual(), decorator somente_admin
app/controllers/  camada HTTP (1 namespace por recurso)
app/services/     regras de negócio, paginação, permissões
app/schemas/      modelos de entrada/saída do flask-restx (senha nunca sai)
app/models/       Empresa, Usuario, Categoria, Fornecedor, Produto, Movimentacao
migrations/       Alembic; 1 revisão (1abc8de16adf, estrutura inicial)
```

## 5. Banco de dados

SQLite por padrão (`sqlite:///estoque.db`); Postgres trocando só `DATABASE_URL` (driver
`psycopg[binary]` já no requirements). Migrations em modo batch (`render_as_batch=True`) e aplicadas
sozinhas ao subir (`AUTO_MIGRATE=1`). FK ligada no SQLite por `PRAGMA` em cada conexão.
Diagrama ER e decisões de modelagem: seção "Modelo de dados" do README.

## 6. API / backend

20 rotas (contadas no `url_map` em 25/09/2026), incluindo `/health`, `/swagger` e `/swagger.json`.
Tabela completa no README, seção "Endpoints". Perfis: `ADMIN` (tudo) e `OPERADOR` (movimenta e
consulta; não exclui produto nem cria fornecedor, usuário ou preço de venda). Códigos: 422 = regra
de negócio violada; 405 = tentar editar movimentação (RN-04); 404 (nunca 403) para recurso de outra empresa.

## 7. Frontend

Ainda não existe: `front-end-cp-python` tem só o README. O CORS já está aberto (`CORS_ORIGINS=*`)
para o front do CP2 rodar em outra porta.

## 8. Segurança (resumo)

Senha com bcrypt, JWT com validade de 8 h, papel checado no servidor, isolamento por empresa vindo
do token. Chaves têm padrão de desenvolvimento em `config.py`: em qualquer ambiente público,
`SECRET_KEY` e `JWT_SECRET_KEY` precisam vir do ambiente. `.env` está no `.gitignore`.

## 10. Testes

**Não há testes automatizados** (nenhum `tests/`, nenhum pytest no requirements). Hoje a prova é o
roteiro manual de 11 passos do README pelo Swagger. Testes automatizados estão previstos para as
próximas entregas.

## 11. Como rodar

```powershell
cd C:\dev\cp-python\backend
python -m venv .venv; .\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe seed.py      # dados demo (opcional)
.\.venv\Scripts\python.exe app.py       # http://127.0.0.1:5000/swagger
```

## 12. Contrato de dados (o que o front vai consumir)

| Elemento | Fonte da verdade |
|---|---|
| Login | `POST /auth/login` `{email, senha}` → `{access_token, usuario}` |
| Autenticação | cabeçalho `Authorization: Bearer <token>` em toda rota exceto register/login |
| Listas | envelope `{itens, pagina, por_pagina, total, total_paginas}`; `?pagina=&por_pagina=` |
| Produto | campos em `app/schemas/produto.py`; `saldo` e `em_ruptura` calculados |
| Movimentação | `tipo` ∈ `ENTRADA`, `SAIDA`, `AJUSTE`; `quantidade` sempre > 0 |
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

## 15. Stack

Backend: Python 3.12+ (testado em 3.14.4), Flask 3.1, flask-restx 1.3, Flask-SQLAlchemy 3.1,
Flask-Migrate 4.1, flask-jwt-extended 4.7, bcrypt 5, flask-cors 6. Banco: SQLite (Postgres opcional).
Frontend, IA, testes e deploy: a definir no CP2.
