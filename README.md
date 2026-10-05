# back-end-cp-python

# Gestor de Estoque — API

API REST para controle de estoque de pequeno comércio. Permite cadastrar produtos, categorias e fornecedores, registrar entradas e saídas, e acompanhar saldo, custo médio e alertas de ruptura.

Projeto acadêmico desenvolvido para a FIAP — Tecnologia em Inteligência Artificial.

---

## Integrantes

| Nome | RM | GitHub |
|---|---|---|
| Felipe Terra | RM569324 | [@terrafelipe](https://github.com/terrafelipe) |
| Gustavo Pugas Linczuk | RM573087 | [@gulinczuk](https://github.com/gulinczuk) |
| Leonardo Bueno | RM572152 | [@leonardobueno1102-droid](https://github.com/leonardobueno1102-droid) |
| João Vitor Veiga | RM569874 | [@JonisMaxWin](https://github.com/JonisMaxWin) |
| Danilo Kheiti | RM574137 | [@DaniloKeithi](https://github.com/DaniloKeithi) |

---

## Stack

| Camada | Tecnologia |
|---|---|
| Linguagem | Python 3.12 ou superior |
| Framework web | Flask |
| API e documentação | flask-restx (Swagger/OpenAPI) |
| ORM | SQLAlchemy |
| Migrations | Alembic (via Flask-Migrate) |
| Banco de dados | SQLite |
| Autenticação | JWT (Flask-JWT-Extended) |
| Hash de senha | bcrypt |

O SQLite foi escolhido por eliminar dependência de servidor externo, mantendo migrations versionadas e integridade referencial. Os modelos usam apenas tipos genéricos do SQLAlchemy, de modo que a migração para PostgreSQL exija apenas a troca da string de conexão.

## Arquitetura

```mermaid
flowchart LR
    F[Front React + Vite<br/>front-end-cp-python] -- HTTP + JWT --> C[controllers<br/>flask-restx]
    C --> S[services<br/>regras RN-xx]
    S --> M[models<br/>SQLAlchemy] --> DB[(SQLite / Postgres)]
    S -- relatório de reposição --> L[Groq LLM]
```

O front consome o contrato de `docs/GRUPO.md`. Toda regra fica em `services/`; o back revalida tudo.

---

## Como rodar

Pré-requisito: **Python 3.12 ou superior**. Nenhum outro serviço é necessário — o banco é um arquivo SQLite criado na primeira execução.

```bash
# 1. Clonar o repositório
git clone https://github.com/<usuario>/<repositorio>.git
cd <repositorio>

# 2. Criar e ativar o ambiente virtual
python -m venv .venv
source .venv/bin/activate        # Linux / macOS
.venv\Scripts\activate          # Windows

# 3. Instalar as dependências
pip install -r requirements.txt

# 4. Popular com dados de demonstração (opcional, mas recomendado)
python seed.py

# 5. Subir a aplicação
python app.py
```

Não é preciso criar `.env` nem rodar `flask db upgrade`: todas as variáveis
têm padrão de desenvolvimento e as migrations pendentes são aplicadas
automaticamente ao subir a aplicação ou ao rodar o seed. Copie o
`.env.example` para `.env` apenas se quiser mudar algum valor — por exemplo,
apontar `DATABASE_URL` para um PostgreSQL.

A API sobe em `http://localhost:5000`.
A documentação interativa fica em **`http://localhost:5000/swagger`**.

### Variáveis de ambiente

Todas são opcionais: o projeto roda sem `.env`.

| Variável | Descrição | Padrão |
|---|---|---|
| `DATABASE_URL` | String de conexão. Trocar de banco é só trocar esta linha. | `sqlite:///estoque.db` na raiz |
| `SECRET_KEY` | Chave da aplicação | chave de desenvolvimento |
| `JWT_SECRET_KEY` | Chave de assinatura dos tokens | o valor de `SECRET_KEY` |
| `JWT_EXPIRES_HOURS` | Validade do token, em horas | `8` |
| `AUTO_MIGRATE` | Aplica as migrations pendentes ao subir | `1` |
| `FLASK_DEBUG` | Recarga automática e log detalhado | `1` |
| `HOST` | Endereço de escuta | `127.0.0.1` |
| `PORT` | Porta | `5000` |
| `SWAGGER_URL` | Caminho da documentação | `/swagger` |
| `SQLALCHEMY_ECHO` | Imprime o SQL gerado, útil para depurar | `0` |
| `CORS_ORIGINS` | Origens aceitas, separadas por vírgula | `*` |
| `GROQ_API_KEY` | Chave da Groq; sem ela o relatório de reposição usa as regras | vazio |
| `GROQ_MODEL` | Modelo da Groq | `openai/gpt-oss-120b` |
| `LLM_TIMEOUT_S` | Segundos até desistir da LLM e usar as regras | `20` |

Para usar PostgreSQL, basta uma linha no `.env` — nenhum arquivo de modelo,
serviço ou migration muda:

```
DATABASE_URL=postgresql+psycopg://usuario:senha@host:5432/estoque
```

### Usuários de demonstração

Criados pelo `seed.py`, que também gera 60 dias de histórico (compras semanais, vendas diárias)
e deixa três produtos em ruptura:

| Email | Senha | Perfil |
|---|---|---|
| `admin@demo.com` | `admin123` | `ADMIN` |
| `operador@demo.com` | `operador123` | `OPERADOR` |

---

## Estrutura do projeto

```
app/
├── __init__.py        # application factory
├── config.py          # configuração por ambiente
├── extensions.py      # db, migrate, jwt
├── errors.py          # tratamento centralizado de erros
├── security.py        # hash de senha, leitura do token e controle de papel
├── models/            # entidades SQLAlchemy
├── schemas/           # modelos de entrada e saída do flask-restx
├── services/          # regras de negócio
└── controllers/       # camada HTTP
migrations/            # histórico de migrations
seed.py                # dados de demonstração
app.py                 # ponto de entrada
```

A arquitetura separa responsabilidades em três camadas: os *controllers* apenas recebem a requisição e devolvem a resposta, os *services* concentram toda a regra de negócio, e os *models* cuidam da persistência. Nenhuma validação de domínio ocorre na camada HTTP — se houvesse verificação de saldo dentro de um controller, estaria no lugar errado.

Duas pastas comuns em outras stacks não existem aqui, por decisão:

| Pasta | Onde ficou | Motivo |
|---|---|---|
| `routers/` | dentro de `controllers/` | No flask-restx a rota é declarada na própria classe (`@ns.route`). Separar exigiria abrir mão do `Resource` e, com ele, da geração automática do Swagger. |
| `middlewares/` | `errors.py` e `security.py` | Em Flask o papel de middleware é cumprido por *error handlers* e *decorators*, que já estão isolados nesses dois módulos. |

---

## Modelo de dados

```mermaid
erDiagram
    EMPRESA ||--o{ USUARIO : possui
    EMPRESA ||--o{ CATEGORIA : possui
    EMPRESA ||--o{ FORNECEDOR : possui
    EMPRESA ||--o{ PRODUTO : possui
    CATEGORIA ||--o{ PRODUTO : classifica
    FORNECEDOR ||--o{ PRODUTO : fornece
    PRODUTO ||--o{ MOVIMENTACAO : registra
    EMPRESA ||--o{ RELATORIO_IA : possui
    USUARIO ||--o{ RELATORIO_IA : gera
    USUARIO ||--o{ MOVIMENTACAO : executa

    EMPRESA {
        int id PK
        string nome
        string cnpj
        string plano
        datetime criado_em
    }
    USUARIO {
        int id PK
        string nome
        string email UK
        string senha_hash
        string role
        bool ativo
        int empresa_id FK
        datetime criado_em
    }
    CATEGORIA {
        int id PK
        string nome
        int empresa_id FK
    }
    FORNECEDOR {
        int id PK
        string nome
        string cnpj
        string email
        string telefone
        int empresa_id FK
    }
    PRODUTO {
        int id PK
        string sku
        string nome
        string descricao
        int categoria_id FK
        int fornecedor_id FK
        decimal preco_custo
        decimal preco_venda
        int estoque_minimo
        string unidade
        bool ativo
        int saldo_atual
        int empresa_id FK
        datetime criado_em
    }
    RELATORIO_IA {
        int id PK
        int empresa_id FK
        int usuario_id FK
        string origem
        string modelo
        json entrada
        json resultado
        datetime criado_em
    }
    MOVIMENTACAO {
        int id PK
        int produto_id FK
        enum tipo
        int quantidade
        decimal custo_unitario
        string motivo
        int usuario_id FK
        datetime criado_em
    }
```

### Decisões de modelagem

**O saldo nasce do histórico.** O valor de referência é a soma das movimentações do item. No CP2 entrou a coluna `saldo_atual` como cache, tratada como desnormalização por desempenho — ver "Revisão do banco (CP2)".

**Multi-tenant desde o início.** Toda entidade de domínio carrega `empresa_id`. Isolar dados por empresa depois que o sistema já tem uso é retrabalho considerável, e essa coluna também sustenta o modelo de planos previsto para etapas seguintes.

**Movimentação como registro imutável.** Movimentações formam a trilha de auditoria do estoque; alterá-las destruiria a capacidade de investigar divergências de inventário.

**Desativação em vez de exclusão, também para usuário.** `usuario` tem a coluna `ativo` pelo mesmo motivo que `produto`: quem já registrou uma movimentação não pode ser apagado sem quebrar a trilha de auditoria — a chave estrangeira recusa. Sem essa coluna, o `DELETE /usuarios/{id}` só funcionaria para quem nunca operou o estoque, justamente o caso que não interessa. É também o que torna verificável a regra de manter ao menos um `ADMIN` **ativo**.

**`AJUSTE` é contagem, não soma.** Uma movimentação do tipo `AJUSTE` **define** o saldo pelo valor informado, em vez de somar a ele. A leitura decorre do próprio modelo: como a quantidade é sempre positiva (RN-03) e a correção precisa poder ir nos dois sentidos (RN-04), um ajuste de sinal fixo não conseguiria baixar o saldo. Na prática é a contagem de inventário — o operador informa o que contou na prateleira, e as movimentações posteriores voltam a somar e subtrair normalmente.

### Revisão do banco (CP2)

**Cache de saldo (`produto.saldo_atual`).** No CP1 o saldo era recalculado do histórico a cada
leitura, e `/estoque/alertas` e `/produtos?em_ruptura=` liam todas as movimentações e filtravam em
Python, sem paginar no banco. O CP2 acrescenta a coluna como desnormalização deliberada, com três
garantias: (1) só `movimentacao_service.registrar` escreve nela, na mesma transação da
movimentação; (2) `CHECK (saldo_atual >= 0)` repete a RN-02 no banco; (3) os testes comparam o
cache com o saldo derivado do histórico depois de entrada, saída e ajuste. A migration preenche a
coluna a partir do histórico existente.

| Índice novo | Atende |
|---|---|
| `produto(empresa_id, ativo)` | toda listagem de produto filtra pela empresa e, por padrão, só ativos |
| `produto(categoria_id)`, `produto(fornecedor_id)` | filtro por categoria e a checagem "em uso" antes de excluir |
| `categoria(empresa_id)`, `fornecedor(empresa_id)`, `usuario(empresa_id)` | listagens por empresa; o UNIQUE composto começa por outra coluna e não serve |
| `movimentacao(usuario_id)` | FK sem índice; auditoria por usuário |
| `relatorio_ia(empresa_id, criado_em)` | último relatório e histórico paginado |

**Tabela `relatorio_ia`.** Cada relatório de reposição fica salvo com a origem (`LLM` ou `REGRAS`),
o modelo, a entrada enviada e o resultado, em JSON. Mostrar o último relatório não chama a LLM de novo.

**Normalização.** O resto segue na 3FN: `movimentacao` continua sem `empresa_id` (a empresa vem do
produto) e `saldo_atual` é a única redundância, documentada acima.

### Otimização (CP2)

Medido com `python scripts/benchmark.py` (SQLite temporário, 500 produtos, 20 mil movimentações,
20 repetições por rota; detalhes em `docs/benchmark-cp2.md`):

| Rota | Antes (mediana) | Depois (mediana) |
|---|---|---|
| `/estoque/alertas` | 176,5 ms | 1,6 ms |
| `/produtos?em_ruptura=true` | 180,4 ms | 1,6 ms |
| `/produtos` | 40,1 ms | 2,4 ms |
| `/estoque/saldo` | 37,2 ms | 2,2 ms |
| `/dashboard/resumo` | — | 26,7 ms |

Três otimizações: (1) cache de saldo, que leva o filtro de ruptura e a paginação para o banco;
(2) dashboard numa requisição só, com as somas feitas em SQL (`SUM`/`COUNT`/`GROUP BY`);
(3) índices nas chaves estrangeiras e em `produto(empresa_id, ativo)`.

---

## Regras de negócio

| Código | Regra | Justificativa |
|---|---|---|
| **RN-01** | O SKU é único dentro de cada empresa | Identificador operacional do produto; duplicidade inviabiliza a conferência física |
| **RN-02** | Saída não pode resultar em saldo negativo | Saldo negativo representa a venda de item inexistente |
| **RN-03** | A quantidade informada é sempre positiva; o sentido vem do campo `tipo` | Evita ambiguidade entre sinal numérico e tipo de operação |
| **RN-04** | Movimentações não podem ser editadas nem excluídas; correções usam o tipo `AJUSTE` | Preserva a trilha de auditoria |
| **RN-05** | Produto com movimentação registrada não é excluído, apenas inativado | Exclusão quebraria o histórico que referencia o item |
| **RN-06** | Produto com saldo abaixo do estoque mínimo é sinalizado como em ruptura | Antecipa a reposição antes da falta |
| **RN-07** | O custo médio ponderado é recalculado a cada entrada | Base para valorização do estoque e apuração de margem |
| **RN-08** | O usuário acessa apenas dados da própria empresa, determinados pelo token | Isolamento entre clientes; validado no servidor, nunca por parâmetro do cliente |
| **RN-09** | Apenas `ADMIN` cria ou altera usuário, fornecedor e preço de venda | Cadastro e política comercial são decisões de gestão, não de operação |
| **RN-10** | O `OPERADOR` registra movimentações e consulta, mas não exclui produto | Quem opera o estoque não decide o que sai do catálogo |

Duas regras adicionais protegem o acesso da empresa, ambas respondendo `422`:
um usuário não pode excluir a si mesmo, e a empresa precisa manter ao menos
um `ADMIN` ativo.

Violações de regra de negócio retornam **HTTP 422** com o código correspondente na resposta.

---

## Endpoints

### Autenticação

| Método | Rota | Descrição |
|---|---|---|
| `POST` | `/auth/register` | Cadastra empresa e usuário administrador |
| `POST` | `/auth/login` | Autentica e retorna o token JWT |
| `GET` | `/auth/me` | Dados do usuário autenticado |

### Usuários

Todas exigem perfil `ADMIN`, exceto a consulta individual.

| Método | Rota | Descrição |
|---|---|---|
| `GET` | `/usuarios` | Lista paginada; `incluir_inativos` traz os desativados |
| `POST` | `/usuarios` | Cadastra usuário na própria empresa |
| `GET` | `/usuarios/{id}` | Detalha um usuário |
| `PUT` | `/usuarios/{id}` | Atualiza usuário; aceita alteração parcial |
| `DELETE` | `/usuarios/{id}` | Desativa o usuário |

### Produtos

| Método | Rota | Descrição |
|---|---|---|
| `GET` | `/produtos` | Lista paginada, com filtros `busca`, `categoria_id` e `em_ruptura` |
| `POST` | `/produtos` | Cadastra produto |
| `GET` | `/produtos/{id}` | Detalha o produto, incluindo o saldo atual |
| `PUT` | `/produtos/{id}` | Atualiza produto |
| `DELETE` | `/produtos/{id}` | Inativa o produto |
| `GET` | `/produtos/{id}/movimentacoes` | Histórico do produto |

### Categorias e fornecedores

| Método | Rota |
|---|---|
| `GET` `POST` | `/categorias` · `/fornecedores` |
| `GET` `PUT` `DELETE` | `/categorias/{id}` · `/fornecedores/{id}` |

### Movimentações e estoque

| Método | Rota | Descrição |
|---|---|---|
| `GET` | `/movimentacoes` | Extrato com filtros `produto_id`, `tipo`, `de` e `ate` |
| `POST` | `/movimentacoes` | Registra entrada, saída ou ajuste |
| `GET` | `/estoque/saldo` | Saldo consolidado de todos os produtos |
| `GET` | `/estoque/alertas` | Produtos abaixo do estoque mínimo |

### Dashboard

| Método | Rota | Descrição |
|---|---|---|
| `GET` | `/dashboard/resumo?dias=30` | KPIs, entradas × saídas por dia, valor por categoria, top 5 saídas e alertas, numa requisição (período de 1 a 365 dias, em UTC) |

### Relatório de reposição (IA)

| Método | Rota | Descrição |
|---|---|---|
| `POST` | `/relatorios/reposicao` | Gera e salva o relatório (LLM ou, sem ela, regras) |
| `GET` | `/relatorios/reposicao/ultimo` | Último relatório, sem nova chamada à LLM (`404` se nunca gerado) |
| `GET` | `/relatorios/reposicao` | Histórico paginado |

Todos os endpoints, exceto `/auth/register` e `/auth/login`, exigem o cabeçalho `Authorization: Bearer <token>`.

---

## Padrões da API

**Códigos de status**

| Código | Uso |
|---|---|
| `200` | Leitura ou atualização bem-sucedida |
| `201` | Recurso criado |
| `204` | Exclusão bem-sucedida |
| `400` | Requisição malformada |
| `401` | Token ausente ou inválido |
| `403` | Sem permissão para o recurso |
| `404` | Recurso inexistente |
| `405` | Método não permitido — usado pela RN-04 em movimentações |
| `422` | Regra de negócio violada |

**Formato de erro**, idêntico em toda a API:

```json
{
  "erro": {
    "codigo": "RN-02",
    "mensagem": "Saída de 50 unidades excede o saldo disponível de 12 unidades.",
    "campo": "quantidade"
  }
}
```

**Formato de listagem**, idêntico em todos os recursos paginados:

```json
{
  "itens": [],
  "pagina": 1,
  "por_pagina": 20,
  "total": 137,
  "total_paginas": 7
}
```

Os campos do JSON seguem `snake_case`. Senhas nunca aparecem em respostas — os modelos de entrada e saída são declarados separadamente.

---

## Relatório de reposição com IA

**Finalidade.** Dizer o que comprar primeiro. O botão "Gerar análise" do dashboard chama
`POST /relatorios/reposicao`; o resultado fica salvo e `GET /relatorios/reposicao/ultimo` o mostra
de novo sem nova chamada.

**Modelo.** `openai/gpt-oss-120b` na Groq (API compatível com a da OpenAI), trocável por
`GROQ_MODEL`. O `llama-3.3-70b-versatile` do plano original saiu da Groq em outubro de 2026. O cliente fica em `app/services/llm/cliente.py`, atrás de uma função.

**Dados enviados.** Só dos produtos ativos em ruptura ou com até 15 dias de cobertura: nome, SKU,
categoria, saldo, estoque mínimo, saídas dos últimos 30 dias, custo médio, dias até acabar e a
quantidade sugerida calculada pelo sistema. Nenhum dado de usuário, e-mail, CNPJ, fornecedor ou
empresa sai do servidor.

**Resposta.** JSON com `resumo` e `prioridades` (`sku`, `motivo`), validado antes de salvar: SKU
desconhecido é descartado, SKU esquecido volta ao fim pela ordem das regras, textos têm tamanho
máximo. Os números (quantidade sugerida) são sempre do sistema — a LLM só ordena e justifica.

**Sem LLM.** Sem `GROQ_API_KEY`, com timeout (`LLM_TIMEOUT_S`) ou resposta inválida, o relatório sai
pelas regras: ordem por dias até acabar e quantidade = maior entre 2× o mínimo e o consumo de 30 dias,
menos o saldo. O campo `origem` diz `LLM` ou `REGRAS` e a tela mostra "gerado por IA" ou "gerado
por regras". Nunca erro 500.

**Limitações.** A justificativa pode ser genérica; a LLM não conhece sazonalidade, preço de
fornecedor nem prazo de entrega. Cotas gratuitas da Groq podem acabar — o relatório por regras cobre.

**Segurança.** O nome do produto é digitado por usuário e pode conter instruções (prompt injection).
Ele vai como dado dentro de um JSON, o prompt manda ignorar ordens escritas nos campos, e a saída é
validada; a LLM não executa nada nem acessa o banco. A chave fica só no `.env`.

---

## Testes

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt   # uma vez
.\.venv\Scripts\python.exe -m pytest -q
```

A suíte usa SQLite em memória, recriado a cada teste, e não acessa a rede (a LLM é simulada).
São 85 testes: RN-01 a RN-10, isolamento entre empresas (401/403/404), cache de saldo igual ao
derivado do histórico, migration com backfill, dashboard, relatório por regras e pela LLM
(sucesso, sem chave, timeout, JSON inválido, SKU inventado, nome com instrução), seed e o
roteiro de validação abaixo, automatizado.

---

## Roteiro de validação

Onze passos para conferir a API inteira pelo `/swagger`. Rode `python seed.py`
antes, e faça login como `admin@demo.com` / `admin123`.

1. **Subir e abrir.** `python app.py` e acesse `http://localhost:5000/swagger`.
   Todas as rotas devem aparecer agrupadas por recurso.
2. **Autenticar.** `POST /auth/login` com o usuário demo. Copie o
   `access_token` da resposta, clique em **Authorize** e informe
   `Bearer <token>`.
3. **Confirmar a identidade.** `GET /auth/me` devolve o usuário do token, sem
   nenhum campo de senha.
4. **Listar produtos.** `GET /produtos` devolve o envelope paginado, e cada
   item traz `saldo` e `em_ruptura` — o saldo vem do cache `saldo_atual`, que
   acompanha cada movimentação.
5. **Ver os alertas.** `GET /estoque/alertas` lista apenas os produtos abaixo
   do estoque mínimo (RN-06). Com os dados do seed, são três.
6. **Registrar uma entrada.** `POST /movimentacoes` com `tipo: ENTRADA`,
   `quantidade: 100` e `custo_unitario`. Consulte o produto de novo: o saldo
   subiu e o `preco_custo` foi recalculado pela média ponderada (RN-07).
7. **Tentar uma saída impossível.** Mesma rota com `tipo: SAIDA` e uma
   quantidade maior que o saldo. A resposta é `422` com o código `RN-02` e a
   quantidade disponível na mensagem.
8. **Tentar alterar o histórico.** `PUT` ou `DELETE` em
   `/movimentacoes/{id}` responde `405` com o código `RN-04`, indicando que a
   correção se faz com um `AJUSTE`.
9. **Testar o papel.** Refaça o login como `operador@demo.com` /
   `operador123`, troque o token no **Authorize** e tente
   `POST /fornecedores` ou `DELETE /produtos/{id}`. Ambos respondem `403`,
   com `RN-09` e `RN-10` respectivamente.
10. **Testar o isolamento.** Crie outra empresa com `POST /auth/register` e,
    com o token dela, tente `GET /produtos/{id}` de um produto da empresa
    demo. A resposta é `404` — nunca `403`, que confirmaria a existência do
    registro (RN-08).
11. **Conferir o padrão de erro.** Qualquer falha acima devolve o mesmo
    envelope: `erro.codigo`, `erro.mensagem` e `erro.campo`. Nenhum stack
    trace chega ao cliente.

---

## Escopo

Esta etapa entrega o backend, a documentação e a persistência. O CP2 entregou dashboard, relatório com LLM, testes automatizados e a revisão do banco; o front está em `front-end-cp-python`. Ficam para depois: containerização e deploy.

Estão deliberadamente **fora do escopo** do produto: emissão de documento fiscal, integração com marketplaces, controle multi-armazém e rastreio por lote ou número de série.

---

## Gestão do projeto

O acompanhamento é feito no Notion, em **[CP1 — Gestor de Estoque](https://app.notion.com/p/3d0acb8b0e44817abed4db77e6486328)**, onde ficam o status de cada item da entrega, a divisão do trabalho em blocos e as decisões técnicas registradas.

O backend foi dividido em quatro blocos, cada um revisado antes do seguinte:

| Bloco | Conteúdo |
|---|---|
| A | Models, migration inicial e tratamento centralizado de erros |
| B | Autenticação, JWT, papéis e CRUD de usuários |
| C | Categorias, fornecedores, produtos, movimentações, saldo e alertas |
| D | Seed, CORS, licença, README e validação final |

O `errors.py` entrou no bloco A de propósito: o formato de erro precisava estar fechado antes da primeira regra que o utiliza.

---

## Licença

Distribuído sob a licença MIT — ver [LICENSE](LICENSE). Projeto de uso
acadêmico.
