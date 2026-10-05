# CP2 — Frontend (F1–F8) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Entregar o front do CP2 em `C:\dev\cp-python\frontend`: login, cadastro, dashboard com gráficos e relatório de IA, CRUDs de produtos, movimentações, categorias, fornecedores e usuários, e 6 fluxos E2E.

**Architecture:** SPA React + Vite + TypeScript. Toda chamada passa por um cliente HTTP único (`src/api/cliente.ts`) que injeta o token, converte o envelope de erro em `ErroDaApi` e desloga no 401. Telas em `src/pages/`, uma por rota; componentes compartilhados em `src/components/`. Dados carregados pelo hook `useConsulta`. Nenhuma regra de negócio no front: ele só esconde menus por papel.

**Tech Stack:** Node 24, Vite 8, React 19, TypeScript, Tailwind 4 (`@tailwindcss/vite`), shadcn 4.21, React Router 7 (`react-router`), Recharts 3, sonner (toasts), Vitest + Testing Library, pytest-playwright (E2E).

**Spec:** `C:\dev\cp-python\backend\docs\SPEC-CP2.md` (seção 6 e critérios 7–8). Contrato: `backend/docs/GRUPO.md`; fonte final: `http://127.0.0.1:5000/swagger.json`.

## Global Constraints

- Repo `C:\dev\cp-python\frontend`, branch `cp2`. Commits pequenos, assunto sem acento, terminando com `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`. **Nunca `git push`** sem ok do Felipe.
- Toda chamada passa por `src/api/cliente.ts`; nunca `fetch` solto em componente.
- Tipos da API em `src/api/tipos.ts`. Preços chegam como **string** (`"27.90"`); valores do dashboard como número.
- Toda operação mostra toast de sucesso; erro mostra `erro.mensagem` e destaca o campo `erro.campo`.
- Toda lista tem estado carregando, vazio e erro (`EstadoLista`).
- Nunca `dangerouslySetInnerHTML`; nenhum segredo no front (só `VITE_API_URL`).
- Textos da interface em pt-BR.
- Token no `localStorage` (D9); 401 com token → limpa o token e volta ao login.
- Menu: OPERADOR não vê Fornecedores nem Usuários; preço de venda só editável por ADMIN; inativar produto só ADMIN.
- Desktop primeiro; no celular o menu vira gaveta (`Sheet`) e tabelas rolam na horizontal (D10).
- Critério de pronto: `npm run lint` e `npm run build` passam; `npm test` passa; E2E passam com back e front locais.

## Review Focus

1. **Token velho no `localStorage`** (back recriado com `seed.py --recriar` ou segredo trocado) → na abertura, `/auth/me` dá 401 e a pessoa cai no login, sem tela quebrada. Teste na Task 2 (cliente) e na Task 3 (`AuthProvider` limpa a sessão).
2. **API fora do ar** → mensagem "Não foi possível falar com a API. Ela está rodando?" em vez de erro em branco. Teste na Task 2.
3. **Erro 401 no próprio login** (senha errada) não pode disparar "sessão expirada" → só desloga se havia token. Teste na Task 2.
4. **Data do dashboard deslocada pelo fuso** (`new Date("2026-09-25")` vira dia 24 no Brasil) → `dataCurta` corta a string, sem `Date`. Teste na Task 2.
5. **Operador abrindo `/usuarios` pela URL** → redireciona para o dashboard (o back daria 403 de qualquer forma). Coberto pelo E2E da Task 8.

---

## Mapa de arquivos

| Arquivo | Task | Responsabilidade |
|---|---|---|
| `package.json`, `vite.config.ts`, `tsconfig*.json`, `components.json`, `src/index.css`, `.env.example`, `src/main.tsx`, `src/App.tsx` | 1 | esqueleto, Tailwind, shadcn, rotas |
| `src/components/ui/*` | 1 | gerados pelo shadcn |
| `src/api/tipos.ts`, `src/api/cliente.ts`, `src/lib/formato.ts`, `src/hooks/useConsulta.ts` + testes | 2 | contrato, HTTP, formatação, carregamento |
| `src/auth/AuthContext.tsx`, `src/auth/Rotas.tsx`, `src/components/Layout.tsx`, `src/components/{EstadoLista,Paginacao,Campo,Selecao,ConfirmarAcao}.tsx`, `src/lib/erros.ts`, `src/pages/{Login,Cadastro}.tsx` | 3 | sessão, menu por papel, peças comuns |
| `src/pages/Dashboard.tsx`, `src/components/dashboard/*` | 4 | F3 |
| `src/pages/Produtos.tsx`, `src/pages/ProdutoHistorico.tsx`, `src/components/produtos/ProdutoDialogo.tsx` | 5 | F4 |
| `src/pages/Movimentacoes.tsx` | 6 | F5 |
| `src/pages/{Categorias,Fornecedores,Usuarios}.tsx` | 7 | F6 |
| `e2e/*` | 8 | F8 |
| `README.md`, `CLAUDE.md` | 1, 9 | docs |

---

### Task 1: Esqueleto (F1)

**Files:**
- Create: projeto Vite em `C:\dev\cp-python\frontend` (sem apagar `CLAUDE.md`, `AGENTS.md`, `.git`), `.env.example`, `src/App.tsx`, `src/main.tsx`, `src/index.css`
- Modify: `README.md`, `.gitignore`

**Interfaces:**
- Produces: alias `@/` → `src/`; componentes shadcn em `@/components/ui/*` (`button input label card table dialog alert-dialog badge sheet skeleton sonner`); `npm run dev|build|lint|test`.

- [ ] **Step 1: Gerar o Vite num diretório temporário e trazer para o repo**

O `create-vite` recusa diretório não vazio. No PowerShell, em `C:\dev\cp-python`:
```powershell
npm create vite@9.2.1 _tmp-front -- --template react-ts
Copy-Item -Recurse -Force _tmp-front\* frontend\
Copy-Item -Force _tmp-front\.gitignore frontend\
```
Depois, num comando separado: `Remove-Item -Recurse -Force _tmp-front`. O `README.md` gerado sobrescreve o atual (só tinha o título); é reescrito no Step 6.

- [ ] **Step 2: Dependências**

Em `frontend`:
```powershell
npm install
npm install react-router@7 recharts@3 sonner@2 lucide-react
npm install -D tailwindcss@4 @tailwindcss/vite@4 @types/node vitest jsdom @testing-library/react @testing-library/jest-dom
```

- [ ] **Step 3: Tailwind, alias e Vitest**

`vite.config.ts`:
```ts
/// <reference types="vitest/config" />
import path from "node:path"
import tailwindcss from "@tailwindcss/vite"
import react from "@vitejs/plugin-react"
import { defineConfig } from "vite"

export default defineConfig({
  plugins: [react(), tailwindcss()],
  resolve: { alias: { "@": path.resolve(__dirname, "./src") } },
  test: { environment: "jsdom", setupFiles: ["./src/teste-setup.ts"] },
})
```
`src/teste-setup.ts`: `import "@testing-library/jest-dom/vitest"`.

`src/index.css` (o shadcn acrescenta as variáveis no Step 4): `@import "tailwindcss";`

Em `tsconfig.json` **e** `tsconfig.app.json`, dentro de `compilerOptions`: `"baseUrl": "."` e `"paths": { "@/*": ["./src/*"] }`. Em `tsconfig.app.json`, acrescentar `"types": ["vitest/globals"]` só se o TypeScript reclamar dos testes.

`package.json`, em `scripts`: `"test": "vitest run"`.

- [ ] **Step 4: shadcn**

```powershell
npx shadcn@4.21.1 init --defaults
npx shadcn@4.21.1 add button input label card table dialog alert-dialog badge sheet skeleton sonner
```
Se o `init` perguntar algo mesmo com `--defaults`, escolher a cor base **Neutral**.

- [ ] **Step 5: App mínimo, `.env.example` e verificação**

`src/main.tsx`:
```tsx
import { StrictMode } from "react"
import { createRoot } from "react-dom/client"
import "./index.css"
import App from "./App"

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <App />
  </StrictMode>,
)
```
`src/App.tsx` (provisório; a Task 3 troca pelas rotas):
```tsx
export default function App() {
  return <main className="p-8 text-2xl font-semibold">Gestor de Estoque</main>
}
```
Apagar `src/App.css` e `src/assets/react.svg` se não forem usados.

`.env.example`:
```
# URL da API Flask (backend). Sem barra no fim.
VITE_API_URL=http://127.0.0.1:5000
```
`.gitignore`: garantir as linhas `.env` e `.env.local` (o template já ignora `*.local`; acrescentar `.env`), e `e2e/.venv/`, `__pycache__/`, `test-results/`.

Run: `npm run lint; npm run build`
Expected: os dois sem erro; `dist/` gerado.

- [ ] **Step 6: README**

`README.md`:
```markdown
# Gestor de Estoque — Front-end (CP2)

Interface web do Gestor de Estoque (checkpoint de Python, FIAP). Consome a API Flask do repositório
[back-end-cp-python](https://github.com/terrafelipe/back-end-cp-python).

## Integrantes

| Nome | RM | GitHub |
|---|---|---|
| Felipe Terra | RM569324 | [@terrafelipe](https://github.com/terrafelipe) |
| Gustavo Pugas Linczuk | RM573087 | [@gulinczuk](https://github.com/gulinczuk) |
| Leonardo Bueno | RM572152 | [@leonardobueno1102-droid](https://github.com/leonardobueno1102-droid) |
| João Vitor Veiga | RM569874 | [@JonisMaxWin](https://github.com/JonisMaxWin) |
| Danilo Kheiti | RM574137 | [@DaniloKeithi](https://github.com/DaniloKeithi) |

## Stack

React 19 + Vite + TypeScript, Tailwind 4 + shadcn/ui, React Router, Recharts, sonner.

## Como rodar

Pré-requisito: a API rodando em `http://127.0.0.1:5000` (ver README do back: `seed.py` e `app.py`).

```powershell
Copy-Item .env.example .env
npm install
npm run dev        # http://localhost:5173
```

Usuários de demonstração: `admin@demo.com` / `admin123` e `operador@demo.com` / `operador123`.

## Checagens

```powershell
npm run lint; npm run build; npm test
```
```

- [ ] **Step 7: Commit**

```bash
git add -A
git commit -F - <<'EOF'
Cria o esqueleto do front com Vite, Tailwind e shadcn

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
EOF
```
Antes do `git add -A`, conferir `git status` sem `.env` nem `node_modules`.

---

### Task 2: Contrato, cliente HTTP, formatação e `useConsulta`

**Files:**
- Create: `src/api/tipos.ts`, `src/api/cliente.ts`, `src/api/cliente.test.ts`, `src/lib/formato.ts`, `src/lib/formato.test.ts`, `src/hooks/useConsulta.ts`

**Interfaces:**
- Produces:
  - Tipos `Papel, Usuario, Pagina<T>, Produto, TipoMovimentacao, Movimentacao, Categoria, Fornecedor, ResumoDashboard, Relatorio, Token`.
  - `class ErroDaApi extends Error { status: number; codigo: string; campo: string | null }`
  - `token.ler(): string | null`, `token.gravar(t: string)`, `token.limpar()`
  - `definirAoDeslogar(fn: () => void)`
  - `api.get<T>(caminho, query?)`, `api.post<T>(caminho, corpo?)`, `api.put<T>(caminho, corpo)`, `api.delete(caminho)`; `query: Record<string, string | number | boolean | null | undefined>` (vazios são omitidos).
  - `dinheiro(v: string | number): string`, `dataHora(iso: string): string`, `dataCurta(isoData: string): string`
  - `useConsulta<T>(carregar: () => Promise<T>, deps: unknown[]): { dados: T | null; erro: ErroDaApi | null; carregando: boolean; recarregar: () => void }`

- [ ] **Step 1: Testes que falham**

`src/api/cliente.test.ts`:
```ts
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest"
import { api, definirAoDeslogar, ErroDaApi, token } from "./cliente"

function responder(status: number, corpo?: unknown) {
  const fetchFalso = vi.fn().mockResolvedValue(
    new Response(corpo === undefined ? null : JSON.stringify(corpo), { status }),
  )
  vi.stubGlobal("fetch", fetchFalso)
  return fetchFalso
}

describe("cliente da API", () => {
  beforeEach(() => localStorage.clear())
  afterEach(() => vi.unstubAllGlobals())

  it("injeta o token e monta a query sem valores vazios", async () => {
    token.gravar("abc")
    const fetchFalso = responder(200, { ok: true })
    await api.get("/produtos", { pagina: 2, busca: "", categoria_id: undefined, em_ruptura: true })
    const [url, init] = fetchFalso.mock.calls[0]
    expect(url).toBe("http://127.0.0.1:5000/produtos?pagina=2&em_ruptura=true")
    expect(init.headers.Authorization).toBe("Bearer abc")
  })

  it("converte o envelope de erro em ErroDaApi com o campo", async () => {
    responder(422, { erro: { codigo: "RN-02", mensagem: "Saída excede o saldo.", campo: "quantidade" } })
    const erro = await api.post("/movimentacoes", {}).catch((e) => e)
    expect(erro).toBeInstanceOf(ErroDaApi)
    expect(erro).toMatchObject({ status: 422, codigo: "RN-02", message: "Saída excede o saldo.", campo: "quantidade" })
  })

  it("401 com token limpa a sessão e avisa", async () => {
    token.gravar("velho")
    const aviso = vi.fn()
    definirAoDeslogar(aviso)
    responder(401, { erro: { codigo: "HTTP-401", mensagem: "Token expirado.", campo: null } })
    await api.get("/auth/me").catch(() => {})
    expect(token.ler()).toBeNull()
    expect(aviso).toHaveBeenCalledOnce()
  })

  it("401 sem token (senha errada no login) não dispara o aviso", async () => {
    const aviso = vi.fn()
    definirAoDeslogar(aviso)
    responder(401, { erro: { codigo: "HTTP-401", mensagem: "E-mail ou senha inválidos.", campo: null } })
    const erro = await api.post("/auth/login", {}).catch((e) => e)
    expect(erro.message).toBe("E-mail ou senha inválidos.")
    expect(aviso).not.toHaveBeenCalled()
  })

  it("API fora do ar vira mensagem clara", async () => {
    vi.stubGlobal("fetch", vi.fn().mockRejectedValue(new TypeError("Failed to fetch")))
    const erro = await api.get("/health").catch((e) => e)
    expect(erro).toMatchObject({ status: 0, codigo: "REDE" })
    expect(erro.message).toContain("Ela está rodando?")
  })

  it("204 devolve undefined", async () => {
    responder(204)
    await expect(api.delete("/produtos/1")).resolves.toBeUndefined()
  })
})
```

`src/lib/formato.test.ts`:
```ts
import { describe, expect, it } from "vitest"
import { dataCurta, dataHora, dinheiro } from "./formato"

describe("formato", () => {
  it("dinheiro aceita string e número", () => {
    expect(dinheiro("27.90")).toBe("R$ 27,90")
    expect(dinheiro(4821.37)).toBe("R$ 4.821,37")
  })
  it("dataCurta não sofre com fuso", () => {
    expect(dataCurta("2026-09-25")).toBe("25/09")
  })
  it("dataHora mostra no fuso local", () => {
    expect(dataHora("2026-09-25T15:30:00+00:00")).toMatch(/^25\/09\/2026 \d{2}:30$/)
  })
})
```
O `Intl` usa espaço sem quebra (U+00A0) depois de "R$"; `dinheiro` troca por espaço comum para o teste e o E2E serem previsíveis.

Run: `npm test`
Expected: FAIL — `Failed to resolve import "./cliente"` / `"./formato"`.

- [ ] **Step 2: `src/api/tipos.ts`**

```ts
export type Papel = "ADMIN" | "OPERADOR"

export interface Usuario {
  id: number
  nome: string
  email: string
  role: Papel
  ativo: boolean
  empresa_id: number
  criado_em: string
}

export interface Token {
  access_token: string
  usuario: Usuario
}

export interface Pagina<T> {
  itens: T[]
  pagina: number
  por_pagina: number
  total: number
  total_paginas: number
}

export interface Produto {
  id: number
  sku: string
  nome: string
  descricao: string | null
  categoria_id: number
  fornecedor_id: number | null
  preco_custo: string
  preco_venda: string
  estoque_minimo: number
  unidade: string
  ativo: boolean
  saldo: number
  em_ruptura: boolean
  criado_em: string
}

export type TipoMovimentacao = "ENTRADA" | "SAIDA" | "AJUSTE"

export interface Movimentacao {
  id: number
  produto_id: number
  tipo: TipoMovimentacao
  quantidade: number
  custo_unitario: string | null
  motivo: string | null
  usuario_id: number
  criado_em: string
}

export interface Categoria {
  id: number
  nome: string
  empresa_id: number
}

export interface Fornecedor {
  id: number
  nome: string
  cnpj: string | null
  email: string | null
  telefone: string | null
  empresa_id: number
}

export interface ResumoDashboard {
  periodo: { de: string; ate: string; dias: number }
  kpis: { valor_estoque: number; produtos_ativos: number; em_ruptura: number; movimentacoes: number }
  serie_diaria: { data: string; entradas: number; saidas: number }[]
  valor_por_categoria: { categoria: string; valor: number }[]
  top_saidas: { produto_id: number; nome: string; quantidade: number }[]
  alertas: Produto[]
}

export interface Relatorio {
  id: number
  origem: "LLM" | "REGRAS"
  modelo: string | null
  criado_em: string
  resultado: {
    resumo: string
    prioridades: { sku: string; nome: string; quantidade_sugerida: number; motivo: string }[]
  }
}
```

- [ ] **Step 3: `src/api/cliente.ts`**

```ts
/** Cliente HTTP único: token, envelope de erro e logout no 401. */

const BASE = (import.meta.env.VITE_API_URL ?? "http://127.0.0.1:5000").replace(/\/$/, "")
const CHAVE_TOKEN = "estoque.token"

export class ErroDaApi extends Error {
  status: number
  codigo: string
  campo: string | null

  constructor(status: number, codigo: string, mensagem: string, campo: string | null) {
    super(mensagem)
    this.name = "ErroDaApi"
    this.status = status
    this.codigo = codigo
    this.campo = campo
  }
}

export const token = {
  ler(): string | null {
    try {
      return localStorage.getItem(CHAVE_TOKEN)
    } catch {
      return null
    }
  },
  gravar(valor: string) {
    localStorage.setItem(CHAVE_TOKEN, valor)
  },
  limpar() {
    localStorage.removeItem(CHAVE_TOKEN)
  },
}

let aoDeslogar: () => void = () => {}

/** Chamado quando a API recusa o token (401): a sessão acabou. */
export function definirAoDeslogar(fn: () => void) {
  aoDeslogar = fn
}

type Query = Record<string, string | number | boolean | null | undefined>

function montarUrl(caminho: string, query?: Query): string {
  const url = new URL(BASE + caminho)
  for (const [chave, valor] of Object.entries(query ?? {})) {
    if (valor !== undefined && valor !== null && valor !== "") url.searchParams.set(chave, String(valor))
  }
  return url.toString()
}

async function requisitar<T>(metodo: string, caminho: string, opcoes: { corpo?: unknown; query?: Query } = {}): Promise<T> {
  const atual = token.ler()
  const headers: Record<string, string> = {}
  if (atual) headers.Authorization = `Bearer ${atual}`
  if (opcoes.corpo !== undefined) headers["Content-Type"] = "application/json"

  let resposta: Response
  try {
    resposta = await fetch(montarUrl(caminho, opcoes.query), {
      method: metodo,
      headers,
      body: opcoes.corpo === undefined ? undefined : JSON.stringify(opcoes.corpo),
    })
  } catch {
    throw new ErroDaApi(0, "REDE", "Não foi possível falar com a API. Ela está rodando?", null)
  }

  if (resposta.status === 204) return undefined as T
  const corpo = await resposta.json().catch(() => null)
  if (!resposta.ok) {
    // Só desloga se havia sessão: 401 no login é senha errada, não sessão expirada.
    if (resposta.status === 401 && atual) {
      token.limpar()
      aoDeslogar()
    }
    const erro = corpo?.erro
    throw new ErroDaApi(
      resposta.status,
      erro?.codigo ?? `HTTP-${resposta.status}`,
      erro?.mensagem ?? "Erro inesperado na API.",
      erro?.campo ?? null,
    )
  }
  return corpo as T
}

export const api = {
  get: <T>(caminho: string, query?: Query) => requisitar<T>("GET", caminho, { query }),
  post: <T>(caminho: string, corpo?: unknown) => requisitar<T>("POST", caminho, { corpo }),
  put: <T>(caminho: string, corpo: unknown) => requisitar<T>("PUT", caminho, { corpo }),
  delete: (caminho: string) => requisitar<void>("DELETE", caminho),
}
```

- [ ] **Step 4: `src/lib/formato.ts`**

```ts
const BRL = new Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL" })
const DATA_HORA = new Intl.DateTimeFormat("pt-BR", { dateStyle: "short", timeStyle: "short" })

export function dinheiro(valor: string | number): string {
  return BRL.format(Number(valor)).replace(/\u00a0/g, " ")
}

export function dataHora(iso: string): string {
  return DATA_HORA.format(new Date(iso)).replace(",", "")
}

/** "2026-09-25" → "25/09" sem passar por Date (que deslocaria o dia pelo fuso). */
export function dataCurta(isoData: string): string {
  const [, mes, dia] = isoData.slice(0, 10).split("-")
  return `${dia}/${mes}`
}
```

- [ ] **Step 5: `src/hooks/useConsulta.ts`**

```ts
import { useEffect, useState } from "react"
import { ErroDaApi } from "@/api/cliente"

function comoErro(e: unknown): ErroDaApi {
  return e instanceof ErroDaApi ? e : new ErroDaApi(0, "DESCONHECIDO", "Erro inesperado.", null)
}

/** Carrega dados quando `deps` mudam. `carregando` sai da chave, sem setState síncrono no efeito. */
export function useConsulta<T>(carregar: () => Promise<T>, deps: unknown[]) {
  const [versao, setVersao] = useState(0)
  const chave = JSON.stringify([deps, versao])
  const [resultado, setResultado] = useState<{ chave: string; dados: T | null; erro: ErroDaApi | null }>({
    chave: "",
    dados: null,
    erro: null,
  })

  useEffect(() => {
    let vivo = true
    carregar().then(
      (dados) => vivo && setResultado({ chave, dados, erro: null }),
      (e) => vivo && setResultado((r) => ({ chave, dados: r.dados, erro: comoErro(e) })),
    )
    return () => {
      vivo = false
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [chave])

  return {
    dados: resultado.dados,
    erro: resultado.chave === chave ? resultado.erro : null,
    carregando: resultado.chave !== chave,
    recarregar: () => setVersao((v) => v + 1),
  }
}
```

- [ ] **Step 6: Rodar**

Run: `npm test; npm run lint; npm run build`
Expected: `9 passed`; lint e build sem erro.

- [ ] **Step 7: Commit**

```bash
git add src/api src/lib src/hooks
git commit -F - <<'EOF'
Cria o cliente HTTP unico, os tipos da API e a formatacao

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
EOF
```

---

### Task 3: Sessão, layout com menu por papel e peças comuns (F2, F7)

**Files:**
- Create: `src/auth/AuthContext.tsx`, `src/auth/Rotas.tsx`, `src/components/Layout.tsx`, `src/components/EstadoLista.tsx`, `src/components/Paginacao.tsx`, `src/components/Campo.tsx`, `src/components/Selecao.tsx`, `src/components/ConfirmarAcao.tsx`, `src/lib/erros.ts`, `src/pages/Login.tsx`, `src/pages/Cadastro.tsx`, `src/components/Layout.test.tsx`
- Modify: `src/App.tsx`

**Interfaces:**
- Consumes: `api`, `token`, `definirAoDeslogar`, `ErroDaApi`, tipos (Task 2).
- Produces:
  - `useSessao(): { usuario: Usuario | null; carregando: boolean; ehAdmin: boolean; entrar(email, senha): Promise<void>; registrar(dados: Registro): Promise<void>; sair(): void }`
  - `<RotaProtegida/>` e `<SoAdmin/>` (elementos de rota com `<Outlet/>`).
  - `<EstadoLista carregando erro vazio mensagemVazia aoTentarDeNovo>{children}</EstadoLista>`
  - `<Paginacao pagina totalPaginas total aoMudar(p)/>`
  - `<Campo rotulo id erro>{input}</Campo>`; `<Selecao id value onChange aria-invalid>{options}</Selecao>` (select nativo estilizado).
  - `<ConfirmarAcao titulo descricao rotulo aoConfirmar gatilho/>`
  - `tratarErro(e: unknown): { campo: string | null; mensagem: string }` — mostra toast de erro e devolve o campo.
  - `erroDo(campo: string, erro: { campo: string | null; mensagem: string } | null): string | undefined`

- [ ] **Step 1: Teste do menu por papel (falha)**

`src/components/Layout.test.tsx`:
```tsx
import { render, screen } from "@testing-library/react"
import { MemoryRouter } from "react-router"
import { describe, expect, it } from "vitest"
import { Menu } from "./Layout"

describe("menu", () => {
  it("operador não vê Fornecedores nem Usuários", () => {
    render(<MemoryRouter><Menu ehAdmin={false} /></MemoryRouter>)
    expect(screen.getByRole("link", { name: "Produtos" })).toBeInTheDocument()
    expect(screen.queryByRole("link", { name: "Usuários" })).toBeNull()
    expect(screen.queryByRole("link", { name: "Fornecedores" })).toBeNull()
  })
  it("admin vê tudo", () => {
    render(<MemoryRouter><Menu ehAdmin /></MemoryRouter>)
    expect(screen.getByRole("link", { name: "Usuários" })).toBeInTheDocument()
  })
})
```
Run: `npm test` → FAIL (`./Layout` não existe).

- [ ] **Step 2: Sessão — `src/auth/AuthContext.tsx`**

```tsx
import { createContext, useContext, useEffect, useState, type ReactNode } from "react"
import { toast } from "sonner"
import { api, definirAoDeslogar, token } from "@/api/cliente"
import type { Token, Usuario } from "@/api/tipos"

export interface Registro {
  empresa: string
  cnpj: string
  nome: string
  email: string
  senha: string
}

interface Sessao {
  usuario: Usuario | null
  carregando: boolean
  ehAdmin: boolean
  entrar(email: string, senha: string): Promise<void>
  registrar(dados: Registro): Promise<void>
  sair(): void
}

const Contexto = createContext<Sessao | null>(null)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [usuario, setUsuario] = useState<Usuario | null>(null)
  const [carregando, setCarregando] = useState(() => token.ler() !== null)

  useEffect(() => {
    definirAoDeslogar(() => {
      setUsuario(null)
      toast.error("Sessão expirada. Entre de novo.")
    })
    if (!token.ler()) return
    // Token salvo pode estar velho (back recriado): /auth/me decide.
    api.get<Usuario>("/auth/me")
      .then(setUsuario, () => token.limpar())
      .finally(() => setCarregando(false))
  }, [])

  function guardar(resposta: Token) {
    token.gravar(resposta.access_token)
    setUsuario(resposta.usuario)
  }

  const valor: Sessao = {
    usuario,
    carregando,
    ehAdmin: usuario?.role === "ADMIN",
    entrar: async (email, senha) => guardar(await api.post<Token>("/auth/login", { email, senha })),
    registrar: async (dados) => guardar(await api.post<Token>("/auth/register", dados)),
    sair: () => {
      token.limpar()
      setUsuario(null)
    },
  }
  return <Contexto.Provider value={valor}>{children}</Contexto.Provider>
}

// eslint-disable-next-line react-refresh/only-export-components
export function useSessao(): Sessao {
  const sessao = useContext(Contexto)
  if (!sessao) throw new Error("useSessao fora do AuthProvider")
  return sessao
}
```

- [ ] **Step 3: Guardas — `src/auth/Rotas.tsx`**

```tsx
import { Navigate, Outlet, useLocation } from "react-router"
import { useSessao } from "./AuthContext"

export function RotaProtegida() {
  const { usuario, carregando } = useSessao()
  const local = useLocation()
  if (carregando) return <p className="p-8 text-muted-foreground">Carregando…</p>
  if (!usuario) return <Navigate to="/login" replace state={{ de: local.pathname }} />
  return <Outlet />
}

/** Atalho de interface: o back recusa de qualquer forma (RN-09). */
export function SoAdmin() {
  const { ehAdmin } = useSessao()
  return ehAdmin ? <Outlet /> : <Navigate to="/" replace />
}
```

- [ ] **Step 4: Peças comuns**

`src/lib/erros.ts`:
```ts
import { toast } from "sonner"
import { ErroDaApi } from "@/api/cliente"

export interface ErroCampo {
  campo: string | null
  mensagem: string
}

/** Mostra o erro da API num toast e devolve o campo para o formulário destacar. */
export function tratarErro(e: unknown): ErroCampo {
  const mensagem = e instanceof ErroDaApi ? e.message : "Erro inesperado."
  toast.error(mensagem)
  return { campo: e instanceof ErroDaApi ? e.campo : null, mensagem }
}

export function erroDo(campo: string, erro: ErroCampo | null): string | undefined {
  return erro?.campo === campo ? erro.mensagem : undefined
}
```

`src/components/Campo.tsx`:
```tsx
import type { ReactNode } from "react"
import { Label } from "@/components/ui/label"

export function Campo({ rotulo, id, erro, children }: { rotulo: string; id: string; erro?: string; children: ReactNode }) {
  return (
    <div className="grid gap-1.5">
      <Label htmlFor={id}>{rotulo}</Label>
      {children}
      {erro && <p role="alert" className="text-sm text-destructive">{erro}</p>}
    </div>
  )
}
```
Cada input recebe `id`, e `aria-invalid={!!erroDo("campo", erro)}` (o shadcn pinta a borda de vermelho).

`src/components/Selecao.tsx`:
```tsx
import type { SelectHTMLAttributes } from "react"
import { cn } from "@/lib/utils"

/** Select nativo com o visual do Input: simples, acessível e fácil de testar. */
export function Selecao({ className, ...props }: SelectHTMLAttributes<HTMLSelectElement>) {
  return (
    <select
      className={cn(
        "h-9 w-full rounded-md border border-input bg-transparent px-3 text-sm shadow-xs outline-none focus-visible:ring-[3px] focus-visible:ring-ring/50 aria-invalid:border-destructive",
        className,
      )}
      {...props}
    />
  )
}
```

`src/components/EstadoLista.tsx`:
```tsx
import type { ReactNode } from "react"
import type { ErroDaApi } from "@/api/cliente"
import { Button } from "@/components/ui/button"
import { Skeleton } from "@/components/ui/skeleton"

interface Props {
  carregando: boolean
  erro: ErroDaApi | null
  vazio: boolean
  mensagemVazia: string
  aoTentarDeNovo: () => void
  children: ReactNode
}

export function EstadoLista({ carregando, erro, vazio, mensagemVazia, aoTentarDeNovo, children }: Props) {
  if (carregando) {
    return (
      <div className="grid gap-2" aria-busy="true">
        {[0, 1, 2].map((i) => <Skeleton key={i} className="h-9 w-full" />)}
      </div>
    )
  }
  if (erro) {
    return (
      <div role="alert" className="rounded-md border border-destructive/40 p-4 text-sm">
        <p>{erro.message}</p>
        <Button variant="outline" size="sm" className="mt-2" onClick={aoTentarDeNovo}>Tentar de novo</Button>
      </div>
    )
  }
  if (vazio) return <p className="py-8 text-center text-sm text-muted-foreground">{mensagemVazia}</p>
  return <>{children}</>
}
```

`src/components/Paginacao.tsx`:
```tsx
import { Button } from "@/components/ui/button"

export function Paginacao({ pagina, totalPaginas, total, aoMudar }: { pagina: number; totalPaginas: number; total: number; aoMudar: (p: number) => void }) {
  if (totalPaginas <= 1) return <p className="mt-3 text-sm text-muted-foreground">{total} item(ns)</p>
  return (
    <div className="mt-3 flex items-center justify-between gap-2 text-sm">
      <span className="text-muted-foreground">{total} item(ns) · página {pagina} de {totalPaginas}</span>
      <div className="flex gap-2">
        <Button variant="outline" size="sm" disabled={pagina <= 1} onClick={() => aoMudar(pagina - 1)}>Anterior</Button>
        <Button variant="outline" size="sm" disabled={pagina >= totalPaginas} onClick={() => aoMudar(pagina + 1)}>Próxima</Button>
      </div>
    </div>
  )
}
```

`src/components/ConfirmarAcao.tsx`:
```tsx
import type { ReactNode } from "react"
import {
  AlertDialog, AlertDialogAction, AlertDialogCancel, AlertDialogContent, AlertDialogDescription,
  AlertDialogFooter, AlertDialogHeader, AlertDialogTitle, AlertDialogTrigger,
} from "@/components/ui/alert-dialog"

export function ConfirmarAcao({ titulo, descricao, rotulo, aoConfirmar, gatilho }: {
  titulo: string; descricao: string; rotulo: string; aoConfirmar: () => void; gatilho: ReactNode
}) {
  return (
    <AlertDialog>
      <AlertDialogTrigger asChild>{gatilho}</AlertDialogTrigger>
      <AlertDialogContent>
        <AlertDialogHeader>
          <AlertDialogTitle>{titulo}</AlertDialogTitle>
          <AlertDialogDescription>{descricao}</AlertDialogDescription>
        </AlertDialogHeader>
        <AlertDialogFooter>
          <AlertDialogCancel>Cancelar</AlertDialogCancel>
          <AlertDialogAction onClick={aoConfirmar}>{rotulo}</AlertDialogAction>
        </AlertDialogFooter>
      </AlertDialogContent>
    </AlertDialog>
  )
}
```

- [ ] **Step 5: Layout — `src/components/Layout.tsx`**

```tsx
import { MenuIcon } from "lucide-react"
import { NavLink, Outlet } from "react-router"
import { useSessao } from "@/auth/AuthContext"
import { Button } from "@/components/ui/button"
import { Sheet, SheetContent, SheetTitle, SheetTrigger } from "@/components/ui/sheet"
import { cn } from "@/lib/utils"

const LINKS = [
  { para: "/", rotulo: "Dashboard", admin: false },
  { para: "/produtos", rotulo: "Produtos", admin: false },
  { para: "/movimentacoes", rotulo: "Movimentações", admin: false },
  { para: "/categorias", rotulo: "Categorias", admin: false },
  { para: "/fornecedores", rotulo: "Fornecedores", admin: true },
  { para: "/usuarios", rotulo: "Usuários", admin: true },
]

export function Menu({ ehAdmin, aoNavegar }: { ehAdmin: boolean; aoNavegar?: () => void }) {
  return (
    <nav className="grid gap-1" aria-label="Menu principal">
      {LINKS.filter((l) => ehAdmin || !l.admin).map((l) => (
        <NavLink
          key={l.para}
          to={l.para}
          end={l.para === "/"}
          onClick={aoNavegar}
          className={({ isActive }) =>
            cn("rounded-md px-3 py-2 text-sm hover:bg-accent", isActive && "bg-accent font-medium")
          }
        >
          {l.rotulo}
        </NavLink>
      ))}
    </nav>
  )
}

export default function Layout() {
  const { usuario, ehAdmin, sair } = useSessao()
  return (
    <div className="min-h-dvh md:grid md:grid-cols-[220px_1fr]">
      <aside className="hidden border-r p-4 md:block">
        <p className="mb-4 px-3 font-semibold">Gestor de Estoque</p>
        <Menu ehAdmin={ehAdmin} />
      </aside>
      <div className="min-w-0">
        <header className="flex items-center justify-between gap-2 border-b px-4 py-3">
          <Sheet>
            <SheetTrigger asChild>
              <Button variant="outline" size="icon" className="md:hidden" aria-label="Abrir menu">
                <MenuIcon />
              </Button>
            </SheetTrigger>
            <SheetContent side="left" className="p-4">
              <SheetTitle>Gestor de Estoque</SheetTitle>
              <Menu ehAdmin={ehAdmin} />
            </SheetContent>
          </Sheet>
          <span className="ml-auto text-sm text-muted-foreground">
            {usuario?.nome} · {usuario?.role}
          </span>
          <Button variant="ghost" size="sm" onClick={sair}>Sair</Button>
        </header>
        <main className="p-4 md:p-6">
          <Outlet />
        </main>
      </div>
    </div>
  )
}
```
Na gaveta, fechar ao navegar: o `SheetContent` fecha sozinho ao trocar de rota se o `Sheet` for controlado. Se não fechar no E2E (Task 8), controlar com `const [aberto, setAberto] = useState(false)` e passar `aoNavegar={() => setAberto(false)}`.

- [ ] **Step 6: Login e cadastro**

`src/pages/Login.tsx`:
```tsx
import { useState, type FormEvent } from "react"
import { Link, Navigate, useLocation, useNavigate } from "react-router"
import { useSessao } from "@/auth/AuthContext"
import { Campo } from "@/components/Campo"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { erroDo, tratarErro, type ErroCampo } from "@/lib/erros"

export default function Login() {
  const { usuario, entrar } = useSessao()
  const navegar = useNavigate()
  const destino = (useLocation().state as { de?: string } | null)?.de ?? "/"
  const [email, setEmail] = useState("")
  const [senha, setSenha] = useState("")
  const [enviando, setEnviando] = useState(false)
  const [erro, setErro] = useState<ErroCampo | null>(null)

  if (usuario) return <Navigate to={destino} replace />

  async function enviar(e: FormEvent) {
    e.preventDefault()
    setEnviando(true)
    try {
      await entrar(email, senha)
      navegar(destino, { replace: true })
    } catch (falha) {
      setErro(tratarErro(falha))
    } finally {
      setEnviando(false)
    }
  }

  return (
    <div className="grid min-h-dvh place-items-center p-4">
      <Card className="w-full max-w-sm">
        <CardHeader><CardTitle>Entrar no Gestor de Estoque</CardTitle></CardHeader>
        <CardContent>
          <form onSubmit={enviar} className="grid gap-4">
            <Campo rotulo="E-mail" id="email" erro={erroDo("email", erro)}>
              <Input id="email" type="email" autoComplete="email" required value={email} onChange={(e) => setEmail(e.target.value)} />
            </Campo>
            <Campo rotulo="Senha" id="senha" erro={erroDo("senha", erro)}>
              <Input id="senha" type="password" autoComplete="current-password" required value={senha} onChange={(e) => setSenha(e.target.value)} />
            </Campo>
            {erro && !erro.campo && <p role="alert" className="text-sm text-destructive">{erro.mensagem}</p>}
            <Button type="submit" disabled={enviando}>{enviando ? "Entrando…" : "Entrar"}</Button>
            <p className="text-center text-sm">Nova empresa? <Link to="/cadastro" className="underline">Cadastre-se</Link></p>
          </form>
        </CardContent>
      </Card>
    </div>
  )
}
```

`src/pages/Cadastro.tsx`:
```tsx
import { useState, type FormEvent } from "react"
import { Link, Navigate, useNavigate } from "react-router"
import { toast } from "sonner"
import { useSessao, type Registro } from "@/auth/AuthContext"
import { Campo } from "@/components/Campo"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { erroDo, tratarErro, type ErroCampo } from "@/lib/erros"

const CAMPOS: { nome: keyof Registro; rotulo: string; tipo: string }[] = [
  { nome: "empresa", rotulo: "Nome da empresa", tipo: "text" },
  { nome: "cnpj", rotulo: "CNPJ", tipo: "text" },
  { nome: "nome", rotulo: "Seu nome", tipo: "text" },
  { nome: "email", rotulo: "E-mail", tipo: "email" },
  { nome: "senha", rotulo: "Senha", tipo: "password" },
]

export default function Cadastro() {
  const { usuario, registrar } = useSessao()
  const navegar = useNavigate()
  const [dados, setDados] = useState<Registro>({ empresa: "", cnpj: "", nome: "", email: "", senha: "" })
  const [enviando, setEnviando] = useState(false)
  const [erro, setErro] = useState<ErroCampo | null>(null)

  if (usuario) return <Navigate to="/" replace />

  async function enviar(e: FormEvent) {
    e.preventDefault()
    setEnviando(true)
    try {
      await registrar(dados)
      toast.success("Empresa cadastrada. Você é o administrador.")
      navegar("/", { replace: true })
    } catch (falha) {
      setErro(tratarErro(falha))
    } finally {
      setEnviando(false)
    }
  }

  return (
    <div className="grid min-h-dvh place-items-center p-4">
      <Card className="w-full max-w-md">
        <CardHeader><CardTitle>Cadastrar empresa</CardTitle></CardHeader>
        <CardContent>
          <form onSubmit={enviar} className="grid gap-4">
            {CAMPOS.map((c) => (
              <Campo key={c.nome} rotulo={c.rotulo} id={c.nome} erro={erroDo(c.nome, erro)}>
                <Input
                  id={c.nome} type={c.tipo} required value={dados[c.nome]}
                  aria-invalid={!!erroDo(c.nome, erro)}
                  onChange={(e) => setDados({ ...dados, [c.nome]: e.target.value })}
                />
              </Campo>
            ))}
            <Button type="submit" disabled={enviando}>{enviando ? "Cadastrando…" : "Cadastrar"}</Button>
            <p className="text-center text-sm">Já tem conta? <Link to="/login" className="underline">Entrar</Link></p>
          </form>
        </CardContent>
      </Card>
    </div>
  )
}
```

- [ ] **Step 7: Rotas — `src/App.tsx`**

As páginas das Tasks 4–7 entram aqui como placeholders e cada task troca o seu.
```tsx
import { BrowserRouter, Navigate, Route, Routes } from "react-router"
import { AuthProvider } from "@/auth/AuthContext"
import { RotaProtegida, SoAdmin } from "@/auth/Rotas"
import Layout from "@/components/Layout"
import { Toaster } from "@/components/ui/sonner"
import Cadastro from "@/pages/Cadastro"
import Login from "@/pages/Login"

function EmBreve({ titulo }: { titulo: string }) {
  return <h1 className="text-2xl font-semibold">{titulo}</h1>
}

export default function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route path="/cadastro" element={<Cadastro />} />
          <Route element={<RotaProtegida />}>
            <Route element={<Layout />}>
              <Route index element={<EmBreve titulo="Dashboard" />} />
              <Route path="produtos" element={<EmBreve titulo="Produtos" />} />
              <Route path="movimentacoes" element={<EmBreve titulo="Movimentações" />} />
              <Route path="categorias" element={<EmBreve titulo="Categorias" />} />
              <Route element={<SoAdmin />}>
                <Route path="fornecedores" element={<EmBreve titulo="Fornecedores" />} />
                <Route path="usuarios" element={<EmBreve titulo="Usuários" />} />
              </Route>
            </Route>
          </Route>
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
        <Toaster richColors position="top-right" />
      </AuthProvider>
    </BrowserRouter>
  )
}
```

- [ ] **Step 8: Rodar e conferir no navegador**

Run: `npm test; npm run lint; npm run build`
Expected: `11 passed`; lint e build sem erro.

Com o back de pé (`backend`: `.venv/Scripts/python.exe app.py`) e `npm run dev`: entrar com `admin@demo.com/admin123` → "Dashboard" e menu com 6 itens; sair; entrar como operador → 4 itens; abrir `/usuarios` → volta ao dashboard; senha errada → toast "E-mail ou senha inválidos." e nenhum "Sessão expirada".

- [ ] **Step 9: Commit**

```bash
git add src
git commit -F - <<'EOF'
Adiciona login, cadastro, rotas protegidas e menu por papel

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
EOF
```

---

### Task 4: Dashboard (F3)

Antes de escrever o gráfico, carregar as skills `dataviz` e `impeccable` (regra do Felipe para interface e gráficos) e ajustar cores e espaçamento ao que elas pedirem, sem mudar a estrutura abaixo.

**Files:**
- Create: `src/pages/Dashboard.tsx`, `src/components/dashboard/Kpis.tsx`, `src/components/dashboard/Graficos.tsx`, `src/components/dashboard/RelatorioCard.tsx`
- Modify: `src/App.tsx` (rota index)

**Interfaces:**
- Consumes: `api`, `useConsulta`, `EstadoLista`, `dinheiro`, `dataCurta`, `dataHora`, `tratarErro`, tipos `ResumoDashboard`, `Relatorio`, `Produto`.
- Produces: rota `/` com `data-testid="kpi-<chave>"` em cada KPI (usado no E2E).

- [ ] **Step 1: KPIs — `src/components/dashboard/Kpis.tsx`**

```tsx
import type { ResumoDashboard } from "@/api/tipos"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { dinheiro } from "@/lib/formato"

export function Kpis({ kpis }: { kpis: ResumoDashboard["kpis"] }) {
  const itens = [
    { chave: "valor_estoque", rotulo: "Valor em estoque", valor: dinheiro(kpis.valor_estoque) },
    { chave: "produtos_ativos", rotulo: "Produtos ativos", valor: String(kpis.produtos_ativos) },
    { chave: "em_ruptura", rotulo: "Em ruptura", valor: String(kpis.em_ruptura) },
    { chave: "movimentacoes", rotulo: "Movimentações no período", valor: String(kpis.movimentacoes) },
  ]
  return (
    <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
      {itens.map((k) => (
        <Card key={k.chave} data-testid={`kpi-${k.chave}`}>
          <CardHeader className="pb-1"><CardTitle className="text-sm font-medium text-muted-foreground">{k.rotulo}</CardTitle></CardHeader>
          <CardContent><p className="text-2xl font-semibold tabular-nums">{k.valor}</p></CardContent>
        </Card>
      ))}
    </div>
  )
}
```

- [ ] **Step 2: Gráficos — `src/components/dashboard/Graficos.tsx`**

```tsx
import { Bar, BarChart, CartesianGrid, Legend, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts"
import type { ResumoDashboard } from "@/api/tipos"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { dataCurta, dinheiro } from "@/lib/formato"

function Painel({ titulo, children, vazio }: { titulo: string; children: React.ReactElement; vazio: boolean }) {
  return (
    <Card>
      <CardHeader><CardTitle className="text-base">{titulo}</CardTitle></CardHeader>
      <CardContent className="h-64">
        {vazio
          ? <p className="grid h-full place-items-center text-sm text-muted-foreground">Sem dados no período.</p>
          : <ResponsiveContainer width="100%" height="100%">{children}</ResponsiveContainer>}
      </CardContent>
    </Card>
  )
}

export function EntradasSaidas({ serie }: { serie: ResumoDashboard["serie_diaria"] }) {
  const vazio = serie.every((p) => p.entradas === 0 && p.saidas === 0)
  return (
    <Painel titulo="Entradas × saídas por dia" vazio={vazio}>
      <LineChart data={serie}>
        <CartesianGrid strokeDasharray="3 3" vertical={false} />
        <XAxis dataKey="data" tickFormatter={dataCurta} minTickGap={16} />
        <YAxis allowDecimals={false} width={40} />
        <Tooltip labelFormatter={(d) => dataCurta(String(d))} />
        <Legend />
        <Line type="monotone" dataKey="entradas" name="Entradas" stroke="var(--chart-1)" dot={false} strokeWidth={2} />
        <Line type="monotone" dataKey="saidas" name="Saídas" stroke="var(--chart-2)" dot={false} strokeWidth={2} />
      </LineChart>
    </Painel>
  )
}

export function ValorPorCategoria({ dados }: { dados: ResumoDashboard["valor_por_categoria"] }) {
  return (
    <Painel titulo="Valor em estoque por categoria" vazio={dados.length === 0}>
      <BarChart data={dados}>
        <CartesianGrid strokeDasharray="3 3" vertical={false} />
        <XAxis dataKey="categoria" />
        <YAxis width={70} tickFormatter={(v) => dinheiro(v).replace(",00", "")} />
        <Tooltip formatter={(v) => dinheiro(Number(v))} />
        <Bar dataKey="valor" name="Valor" fill="var(--chart-1)" radius={[4, 4, 0, 0]} />
      </BarChart>
    </Painel>
  )
}

export function TopSaidas({ dados }: { dados: ResumoDashboard["top_saidas"] }) {
  return (
    <Painel titulo="Top 5 saídas no período" vazio={dados.length === 0}>
      <BarChart data={dados} layout="vertical" margin={{ left: 8 }}>
        <CartesianGrid strokeDasharray="3 3" horizontal={false} />
        <XAxis type="number" allowDecimals={false} />
        <YAxis type="category" dataKey="nome" width={140} />
        <Tooltip />
        <Bar dataKey="quantidade" name="Unidades" fill="var(--chart-2)" radius={[0, 4, 4, 0]} />
      </BarChart>
    </Painel>
  )
}
```

- [ ] **Step 3: Relatório — `src/components/dashboard/RelatorioCard.tsx`**

```tsx
import { useState } from "react"
import { toast } from "sonner"
import { api, ErroDaApi } from "@/api/cliente"
import type { Relatorio } from "@/api/tipos"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { useConsulta } from "@/hooks/useConsulta"
import { tratarErro } from "@/lib/erros"
import { dataHora } from "@/lib/formato"

/** Último relatório salvo (sem chamar a LLM) e o botão que gera um novo. */
async function ultimo(): Promise<Relatorio | null> {
  try {
    return await api.get<Relatorio>("/relatorios/reposicao/ultimo")
  } catch (e) {
    if (e instanceof ErroDaApi && e.status === 404) return null
    throw e
  }
}

export function RelatorioCard() {
  const salvo = useConsulta(ultimo, [])
  const [novo, setNovo] = useState<Relatorio | null>(null)
  const [gerando, setGerando] = useState(false)
  const relatorio = novo ?? salvo.dados

  async function gerar() {
    setGerando(true)
    try {
      setNovo(await api.post<Relatorio>("/relatorios/reposicao"))
      toast.success("Análise gerada.")
    } catch (e) {
      tratarErro(e)
    } finally {
      setGerando(false)
    }
  }

  return (
    <Card>
      <CardHeader className="flex flex-row flex-wrap items-center justify-between gap-2">
        <CardTitle className="text-base">Análise de reposição</CardTitle>
        <Button onClick={gerar} disabled={gerando}>{gerando ? "Gerando análise…" : "Gerar análise"}</Button>
      </CardHeader>
      <CardContent className="grid gap-3 text-sm">
        {salvo.carregando && !novo && <p className="text-muted-foreground">Carregando…</p>}
        {!salvo.carregando && !relatorio && <p className="text-muted-foreground">Nenhuma análise gerada ainda.</p>}
        {relatorio && (
          <>
            <div className="flex flex-wrap items-center gap-2">
              <Badge variant={relatorio.origem === "LLM" ? "default" : "secondary"}>
                {relatorio.origem === "LLM" ? "gerado por IA" : "gerado por regras"}
              </Badge>
              <span className="text-muted-foreground">
                {dataHora(relatorio.criado_em)}{relatorio.modelo ? ` · ${relatorio.modelo}` : ""}
              </span>
            </div>
            <p>{relatorio.resultado.resumo}</p>
            <ol className="grid gap-2">
              {relatorio.resultado.prioridades.map((p, i) => (
                <li key={p.sku} className="rounded-md border p-2">
                  <p className="font-medium">{i + 1}. {p.nome} <span className="text-muted-foreground">({p.sku})</span> — comprar {p.quantidade_sugerida}</p>
                  <p className="text-muted-foreground">{p.motivo}</p>
                </li>
              ))}
            </ol>
          </>
        )}
      </CardContent>
    </Card>
  )
}
```

- [ ] **Step 4: Página — `src/pages/Dashboard.tsx`**

```tsx
import { useState } from "react"
import { api } from "@/api/cliente"
import type { ResumoDashboard } from "@/api/tipos"
import { EntradasSaidas, TopSaidas, ValorPorCategoria } from "@/components/dashboard/Graficos"
import { Kpis } from "@/components/dashboard/Kpis"
import { RelatorioCard } from "@/components/dashboard/RelatorioCard"
import { EstadoLista } from "@/components/EstadoLista"
import { Selecao } from "@/components/Selecao"
import { Badge } from "@/components/ui/badge"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { useConsulta } from "@/hooks/useConsulta"

export default function Dashboard() {
  const [dias, setDias] = useState(30)
  const resumo = useConsulta(() => api.get<ResumoDashboard>("/dashboard/resumo", { dias }), [dias])
  const r = resumo.dados

  return (
    <div className="grid gap-6">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <h1 className="text-2xl font-semibold">Dashboard</h1>
        <label className="flex items-center gap-2 text-sm">
          Período
          <Selecao className="w-32" value={dias} onChange={(e) => setDias(Number(e.target.value))}>
            <option value={7}>7 dias</option>
            <option value={30}>30 dias</option>
            <option value={90}>90 dias</option>
          </Selecao>
        </label>
      </div>
      <EstadoLista carregando={resumo.carregando} erro={resumo.erro} vazio={false} mensagemVazia="" aoTentarDeNovo={resumo.recarregar}>
        {r && (
          <>
            <Kpis kpis={r.kpis} />
            <div className="grid gap-4 lg:grid-cols-2">
              <EntradasSaidas serie={r.serie_diaria} />
              <ValorPorCategoria dados={r.valor_por_categoria} />
              <TopSaidas dados={r.top_saidas} />
              <Card>
                <CardHeader><CardTitle className="text-base">Alertas de ruptura</CardTitle></CardHeader>
                <CardContent className="overflow-x-auto">
                  {r.alertas.length === 0 ? (
                    <p className="text-sm text-muted-foreground">Nenhum produto abaixo do mínimo.</p>
                  ) : (
                    <Table>
                      <TableHeader><TableRow><TableHead>Produto</TableHead><TableHead className="text-right">Saldo</TableHead><TableHead className="text-right">Mínimo</TableHead></TableRow></TableHeader>
                      <TableBody>
                        {r.alertas.map((p) => (
                          <TableRow key={p.id}>
                            <TableCell>{p.nome} <Badge variant="destructive" className="ml-1">ruptura</Badge></TableCell>
                            <TableCell className="text-right tabular-nums">{p.saldo}</TableCell>
                            <TableCell className="text-right tabular-nums">{p.estoque_minimo}</TableCell>
                          </TableRow>
                        ))}
                      </TableBody>
                    </Table>
                  )}
                </CardContent>
              </Card>
            </div>
          </>
        )}
      </EstadoLista>
      <RelatorioCard />
    </div>
  )
}
```
`src/App.tsx`: importar `Dashboard` e trocar `<EmBreve titulo="Dashboard" />` por `<Dashboard />`.

O dashboard faz só `/dashboard/resumo` (e `/relatorios/reposicao/ultimo`): critério 4 da SPEC.

- [ ] **Step 5: Conferir**

Run: `npm run lint; npm run build`
Expected: sem erro. No navegador (back com `seed.py --recriar`): KPIs com "Em ruptura" = 3, linha com 30 pontos, 4 barras de categoria, top 5, 3 alertas; trocar para 7 dias recarrega; "Gerar análise" sem `GROQ_API_KEY` mostra "gerado por regras" com 3+ prioridades. Aba Network: só `resumo` e `ultimo`.

- [ ] **Step 6: Commit**

```bash
git add src
git commit -F - <<'EOF'
Cria o dashboard com KPIs, graficos, alertas e analise de reposicao

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
EOF
```

---

### Task 5: Produtos (F4)

**Files:**
- Create: `src/pages/Produtos.tsx`, `src/pages/ProdutoHistorico.tsx`, `src/components/produtos/ProdutoDialogo.tsx`, `src/hooks/useCatalogo.ts`
- Modify: `src/App.tsx` (rotas `produtos` e `produtos/:id`)

**Interfaces:**
- Consumes: Tasks 2–3.
- Produces: `useCatalogo(): { categorias: Categoria[]; fornecedores: Fornecedor[] }` (fornecedores vazio se a API recusar), usado também pela Task 6? Não — a Task 6 só usa produtos.

- [ ] **Step 1: `src/hooks/useCatalogo.ts`**

```ts
import { api } from "@/api/cliente"
import type { Categoria, Fornecedor, Pagina } from "@/api/tipos"
import { useConsulta } from "./useConsulta"

/** Categorias e fornecedores para selects (até 100, o máximo da API). */
export function useCatalogo() {
  const categorias = useConsulta(() => api.get<Pagina<Categoria>>("/categorias", { por_pagina: 100 }), [])
  const fornecedores = useConsulta(
    () => api.get<Pagina<Fornecedor>>("/fornecedores", { por_pagina: 100 }).catch(() => null),
    [],
  )
  return { categorias: categorias.dados?.itens ?? [], fornecedores: fornecedores.dados?.itens ?? [] }
}
```

- [ ] **Step 2: Diálogo — `src/components/produtos/ProdutoDialogo.tsx`**

```tsx
import { useState, type FormEvent, type ReactNode } from "react"
import { toast } from "sonner"
import { api } from "@/api/cliente"
import type { Categoria, Fornecedor, Produto } from "@/api/tipos"
import { useSessao } from "@/auth/AuthContext"
import { Campo } from "@/components/Campo"
import { Selecao } from "@/components/Selecao"
import { Button } from "@/components/ui/button"
import { Dialog, DialogContent, DialogFooter, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog"
import { Input } from "@/components/ui/input"
import { erroDo, tratarErro, type ErroCampo } from "@/lib/erros"

interface Props {
  produto?: Produto
  categorias: Categoria[]
  fornecedores: Fornecedor[]
  aoSalvar: () => void
  gatilho: ReactNode
}

function inicial(p?: Produto) {
  return {
    sku: p?.sku ?? "", nome: p?.nome ?? "", descricao: p?.descricao ?? "",
    categoria_id: p ? String(p.categoria_id) : "", fornecedor_id: p?.fornecedor_id ? String(p.fornecedor_id) : "",
    estoque_minimo: String(p?.estoque_minimo ?? 0), unidade: p?.unidade ?? "UN", preco_venda: p?.preco_venda ?? "",
  }
}

export function ProdutoDialogo({ produto, categorias, fornecedores, aoSalvar, gatilho }: Props) {
  const { ehAdmin } = useSessao()
  const [aberto, setAberto] = useState(false)
  const [form, setForm] = useState(() => inicial(produto))
  const [erro, setErro] = useState<ErroCampo | null>(null)
  const [enviando, setEnviando] = useState(false)
  const alterar = (campo: keyof typeof form) => (e: { target: { value: string } }) => setForm({ ...form, [campo]: e.target.value })

  async function enviar(e: FormEvent) {
    e.preventDefault()
    setEnviando(true)
    const corpo: Record<string, unknown> = {
      sku: form.sku, nome: form.nome, descricao: form.descricao || null,
      categoria_id: Number(form.categoria_id), fornecedor_id: form.fornecedor_id ? Number(form.fornecedor_id) : null,
      estoque_minimo: Number(form.estoque_minimo), unidade: form.unidade,
    }
    // Operador não envia preço de venda: o back recusaria (RN-09).
    if (ehAdmin && form.preco_venda !== "") corpo.preco_venda = Number(form.preco_venda)
    try {
      if (produto) await api.put(`/produtos/${produto.id}`, corpo)
      else await api.post("/produtos", corpo)
      toast.success(produto ? "Produto atualizado." : "Produto criado.")
      setAberto(false)
      if (!produto) setForm(inicial())
      setErro(null)
      aoSalvar()
    } catch (falha) {
      setErro(tratarErro(falha))
    } finally {
      setEnviando(false)
    }
  }

  return (
    <Dialog open={aberto} onOpenChange={(a) => { setAberto(a); if (a) { setForm(inicial(produto)); setErro(null) } }}>
      <DialogTrigger asChild>{gatilho}</DialogTrigger>
      <DialogContent className="max-h-[90dvh] overflow-y-auto">
        <DialogHeader><DialogTitle>{produto ? "Editar produto" : "Novo produto"}</DialogTitle></DialogHeader>
        <form onSubmit={enviar} className="grid gap-3">
          <div className="grid gap-3 sm:grid-cols-2">
            <Campo rotulo="SKU" id="sku" erro={erroDo("sku", erro)}>
              <Input id="sku" required value={form.sku} onChange={alterar("sku")} aria-invalid={!!erroDo("sku", erro)} />
            </Campo>
            <Campo rotulo="Unidade" id="unidade" erro={erroDo("unidade", erro)}>
              <Input id="unidade" value={form.unidade} onChange={alterar("unidade")} />
            </Campo>
          </div>
          <Campo rotulo="Nome" id="nome" erro={erroDo("nome", erro)}>
            <Input id="nome" required value={form.nome} onChange={alterar("nome")} aria-invalid={!!erroDo("nome", erro)} />
          </Campo>
          <Campo rotulo="Categoria" id="categoria_id" erro={erroDo("categoria_id", erro)}>
            <Selecao id="categoria_id" required value={form.categoria_id} onChange={alterar("categoria_id")} aria-invalid={!!erroDo("categoria_id", erro)}>
              <option value="">Selecione…</option>
              {categorias.map((c) => <option key={c.id} value={c.id}>{c.nome}</option>)}
            </Selecao>
          </Campo>
          <Campo rotulo="Fornecedor" id="fornecedor_id" erro={erroDo("fornecedor_id", erro)}>
            <Selecao id="fornecedor_id" value={form.fornecedor_id} onChange={alterar("fornecedor_id")}>
              <option value="">Nenhum</option>
              {fornecedores.map((f) => <option key={f.id} value={f.id}>{f.nome}</option>)}
            </Selecao>
          </Campo>
          <div className="grid gap-3 sm:grid-cols-2">
            <Campo rotulo="Estoque mínimo" id="estoque_minimo" erro={erroDo("estoque_minimo", erro)}>
              <Input id="estoque_minimo" type="number" min={0} value={form.estoque_minimo} onChange={alterar("estoque_minimo")} aria-invalid={!!erroDo("estoque_minimo", erro)} />
            </Campo>
            <Campo rotulo="Preço de venda (R$)" id="preco_venda" erro={erroDo("preco_venda", erro) ?? (ehAdmin ? undefined : "Só o administrador altera o preço.")}>
              <Input id="preco_venda" type="number" step="0.01" min={0} disabled={!ehAdmin} value={form.preco_venda} onChange={alterar("preco_venda")} />
            </Campo>
          </div>
          <Campo rotulo="Descrição" id="descricao" erro={erroDo("descricao", erro)}>
            <Input id="descricao" value={form.descricao} onChange={alterar("descricao")} />
          </Campo>
          <DialogFooter><Button type="submit" disabled={enviando}>{enviando ? "Salvando…" : "Salvar"}</Button></DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  )
}
```
O aviso "Só o administrador altera o preço." usa o slot de erro do `Campo` só por economia; se o `role="alert"` atrapalhar leitores de tela, trocar por um `<p>` comum dentro do `Campo`.

- [ ] **Step 3: Lista — `src/pages/Produtos.tsx`**

```tsx
import { useState, type FormEvent } from "react"
import { Link } from "react-router"
import { toast } from "sonner"
import { api } from "@/api/cliente"
import type { Pagina, Produto } from "@/api/tipos"
import { useSessao } from "@/auth/AuthContext"
import { ConfirmarAcao } from "@/components/ConfirmarAcao"
import { EstadoLista } from "@/components/EstadoLista"
import { Paginacao } from "@/components/Paginacao"
import { ProdutoDialogo } from "@/components/produtos/ProdutoDialogo"
import { Selecao } from "@/components/Selecao"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { useCatalogo } from "@/hooks/useCatalogo"
import { useConsulta } from "@/hooks/useConsulta"
import { tratarErro } from "@/lib/erros"
import { dinheiro } from "@/lib/formato"

export default function Produtos() {
  const { ehAdmin } = useSessao()
  const { categorias, fornecedores } = useCatalogo()
  const [texto, setTexto] = useState("")
  const [filtros, setFiltros] = useState({ busca: "", categoria_id: "", em_ruptura: "", pagina: 1 })
  const lista = useConsulta(
    () => api.get<Pagina<Produto>>("/produtos", { ...filtros, por_pagina: 20 }),
    [filtros],
  )
  const nomeCategoria = (id: number) => categorias.find((c) => c.id === id)?.nome ?? "—"

  function buscar(e: FormEvent) {
    e.preventDefault()
    setFiltros({ ...filtros, busca: texto, pagina: 1 })
  }

  async function inativar(p: Produto) {
    try {
      await api.delete(`/produtos/${p.id}`)
      toast.success(`${p.nome} inativado.`)
      lista.recarregar()
    } catch (e) {
      tratarErro(e)
    }
  }

  return (
    <div className="grid gap-4">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <h1 className="text-2xl font-semibold">Produtos</h1>
        <ProdutoDialogo categorias={categorias} fornecedores={fornecedores} aoSalvar={lista.recarregar} gatilho={<Button>Novo produto</Button>} />
      </div>
      <form onSubmit={buscar} className="grid gap-2 sm:grid-cols-[1fr_200px_180px_auto]">
        <Input placeholder="Buscar por nome ou SKU" aria-label="Buscar" value={texto} onChange={(e) => setTexto(e.target.value)} />
        <Selecao aria-label="Categoria" value={filtros.categoria_id} onChange={(e) => setFiltros({ ...filtros, categoria_id: e.target.value, pagina: 1 })}>
          <option value="">Todas as categorias</option>
          {categorias.map((c) => <option key={c.id} value={c.id}>{c.nome}</option>)}
        </Selecao>
        <Selecao aria-label="Ruptura" value={filtros.em_ruptura} onChange={(e) => setFiltros({ ...filtros, em_ruptura: e.target.value, pagina: 1 })}>
          <option value="">Todos</option>
          <option value="true">Em ruptura</option>
          <option value="false">Abastecidos</option>
        </Selecao>
        <Button type="submit" variant="outline">Buscar</Button>
      </form>
      <EstadoLista carregando={lista.carregando} erro={lista.erro} vazio={lista.dados?.total === 0} mensagemVazia="Nenhum produto encontrado." aoTentarDeNovo={lista.recarregar}>
        {lista.dados && (
          <>
            <div className="overflow-x-auto">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>SKU</TableHead><TableHead>Nome</TableHead><TableHead>Categoria</TableHead>
                    <TableHead className="text-right">Saldo</TableHead><TableHead className="text-right">Mínimo</TableHead>
                    <TableHead className="text-right">Preço</TableHead><TableHead>Ações</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {lista.dados.itens.map((p) => (
                    <TableRow key={p.id}>
                      <TableCell className="font-mono text-xs">{p.sku}</TableCell>
                      <TableCell>{p.nome} {p.em_ruptura && <Badge variant="destructive" className="ml-1">ruptura</Badge>}</TableCell>
                      <TableCell>{nomeCategoria(p.categoria_id)}</TableCell>
                      <TableCell className="text-right tabular-nums">{p.saldo}</TableCell>
                      <TableCell className="text-right tabular-nums">{p.estoque_minimo}</TableCell>
                      <TableCell className="text-right tabular-nums">{dinheiro(p.preco_venda)}</TableCell>
                      <TableCell className="flex gap-1">
                        <ProdutoDialogo produto={p} categorias={categorias} fornecedores={fornecedores} aoSalvar={lista.recarregar} gatilho={<Button size="sm" variant="outline">Editar</Button>} />
                        <Button size="sm" variant="ghost" asChild><Link to={`/produtos/${p.id}`}>Histórico</Link></Button>
                        {ehAdmin && (
                          <ConfirmarAcao
                            titulo={`Inativar ${p.nome}?`}
                            descricao="O produto sai das listas e não aceita movimentações. O histórico é mantido."
                            rotulo="Inativar" aoConfirmar={() => inativar(p)}
                            gatilho={<Button size="sm" variant="ghost">Inativar</Button>}
                          />
                        )}
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
            <Paginacao pagina={lista.dados.pagina} totalPaginas={lista.dados.total_paginas} total={lista.dados.total} aoMudar={(pagina) => setFiltros({ ...filtros, pagina })} />
          </>
        )}
      </EstadoLista>
    </div>
  )
}
```

- [ ] **Step 4: Histórico — `src/pages/ProdutoHistorico.tsx`**

```tsx
import { useState } from "react"
import { Link, useParams } from "react-router"
import { api } from "@/api/cliente"
import type { Movimentacao, Pagina, Produto } from "@/api/tipos"
import { EstadoLista } from "@/components/EstadoLista"
import { Paginacao } from "@/components/Paginacao"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { useConsulta } from "@/hooks/useConsulta"
import { dataHora, dinheiro } from "@/lib/formato"

export const ROTULO_TIPO = { ENTRADA: "Entrada", SAIDA: "Saída", AJUSTE: "Ajuste" } as const

export default function ProdutoHistorico() {
  const { id } = useParams()
  const [pagina, setPagina] = useState(1)
  const produto = useConsulta(() => api.get<Produto>(`/produtos/${id}`), [id])
  const movs = useConsulta(
    () => api.get<Pagina<Movimentacao>>(`/produtos/${id}/movimentacoes`, { pagina, por_pagina: 20 }),
    [id, pagina],
  )
  const p = produto.dados

  return (
    <div className="grid gap-4">
      <Link to="/produtos" className="text-sm underline">← Produtos</Link>
      <h1 className="text-2xl font-semibold">{p ? `${p.nome} (${p.sku})` : "Histórico do produto"}</h1>
      {p && <p className="text-sm text-muted-foreground">Saldo {p.saldo} · mínimo {p.estoque_minimo} · custo médio {dinheiro(p.preco_custo)}</p>}
      <EstadoLista carregando={movs.carregando} erro={movs.erro ?? produto.erro} vazio={movs.dados?.total === 0} mensagemVazia="Sem movimentações." aoTentarDeNovo={movs.recarregar}>
        {movs.dados && (
          <>
            <div className="overflow-x-auto">
              <Table>
                <TableHeader><TableRow><TableHead>Data</TableHead><TableHead>Tipo</TableHead><TableHead className="text-right">Qtd.</TableHead><TableHead className="text-right">Custo</TableHead><TableHead>Motivo</TableHead></TableRow></TableHeader>
                <TableBody>
                  {movs.dados.itens.map((m) => (
                    <TableRow key={m.id}>
                      <TableCell>{dataHora(m.criado_em)}</TableCell>
                      <TableCell>{ROTULO_TIPO[m.tipo]}</TableCell>
                      <TableCell className="text-right tabular-nums">{m.quantidade}</TableCell>
                      <TableCell className="text-right tabular-nums">{m.custo_unitario ? dinheiro(m.custo_unitario) : "—"}</TableCell>
                      <TableCell>{m.motivo ?? "—"}</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
            <Paginacao pagina={movs.dados.pagina} totalPaginas={movs.dados.total_paginas} total={movs.dados.total} aoMudar={setPagina} />
          </>
        )}
      </EstadoLista>
    </div>
  )
}
```
O `export const ROTULO_TIPO` num arquivo de página dispara `react-refresh/only-export-components`; se o lint reclamar, mover para `src/lib/formato.ts` e importar de lá (a Task 6 também usa).

`src/App.tsx`: `produtos` → `<Produtos />` e nova rota `produtos/:id` → `<ProdutoHistorico />`.

- [ ] **Step 5: Conferir**

Run: `npm test; npm run lint; npm run build` → sem erro.
No navegador: criar produto `TESTE-1` → toast "Produto criado." e aparece na lista; SKU repetido → toast com a mensagem RN-01 e campo SKU vermelho; filtro "Em ruptura" → 3 itens; operador vê preço desabilitado e não vê "Inativar"; admin inativa com confirmação; "Histórico" lista as movimentações.

- [ ] **Step 6: Commit**

```bash
git add src
git commit -F - <<'EOF'
Cria a tela de produtos com filtros, dialogo de cadastro e historico

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
EOF
```

---

### Task 6: Movimentações (F5)

**Files:**
- Create: `src/pages/Movimentacoes.tsx`
- Modify: `src/App.tsx`

**Interfaces:**
- Consumes: `ROTULO_TIPO` (Task 5, onde ele estiver), Tasks 2–3.

- [ ] **Step 1: `src/pages/Movimentacoes.tsx`**

```tsx
import { useState, type FormEvent } from "react"
import { toast } from "sonner"
import { api } from "@/api/cliente"
import type { Movimentacao, Pagina, Produto, TipoMovimentacao } from "@/api/tipos"
import { Campo } from "@/components/Campo"
import { EstadoLista } from "@/components/EstadoLista"
import { Paginacao } from "@/components/Paginacao"
import { Selecao } from "@/components/Selecao"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { useConsulta } from "@/hooks/useConsulta"
import { erroDo, tratarErro, type ErroCampo } from "@/lib/erros"
import { dataHora, dinheiro } from "@/lib/formato"
import { ROTULO_TIPO } from "@/pages/ProdutoHistorico"

const VAZIO = { produto_id: "", tipo: "ENTRADA" as TipoMovimentacao, quantidade: "", custo_unitario: "", motivo: "" }

export default function Movimentacoes() {
  const produtos = useConsulta(() => api.get<Pagina<Produto>>("/produtos", { por_pagina: 100 }), [])
  const [form, setForm] = useState(VAZIO)
  const [erro, setErro] = useState<ErroCampo | null>(null)
  const [enviando, setEnviando] = useState(false)
  const [filtros, setFiltros] = useState({ tipo: "", produto_id: "", de: "", ate: "", pagina: 1 })
  const extrato = useConsulta(() => api.get<Pagina<Movimentacao>>("/movimentacoes", { ...filtros, por_pagina: 20 }), [filtros])
  const lista = produtos.dados?.itens ?? []
  const nomeProduto = (id: number) => lista.find((p) => p.id === id)?.nome ?? `#${id}`

  async function registrar(e: FormEvent) {
    e.preventDefault()
    setEnviando(true)
    try {
      await api.post("/movimentacoes", {
        produto_id: Number(form.produto_id),
        tipo: form.tipo,
        quantidade: Number(form.quantidade),
        // Custo só existe em entrada (RN-07).
        custo_unitario: form.tipo === "ENTRADA" && form.custo_unitario ? Number(form.custo_unitario) : null,
        motivo: form.motivo || null,
      })
      toast.success(`${ROTULO_TIPO[form.tipo]} registrada.`)
      setForm({ ...VAZIO, produto_id: form.produto_id, tipo: form.tipo })
      setErro(null)
      extrato.recarregar()
      produtos.recarregar()
    } catch (falha) {
      setErro(tratarErro(falha))
    } finally {
      setEnviando(false)
    }
  }

  const selecionado = lista.find((p) => String(p.id) === form.produto_id)

  return (
    <div className="grid gap-6">
      <h1 className="text-2xl font-semibold">Movimentações</h1>
      <Card>
        <CardHeader><CardTitle className="text-base">Registrar movimentação</CardTitle></CardHeader>
        <CardContent>
          <form onSubmit={registrar} className="grid gap-3 md:grid-cols-[2fr_1fr_1fr_1fr]">
            <Campo rotulo="Produto" id="produto_id" erro={erroDo("produto_id", erro)}>
              <Selecao id="produto_id" required value={form.produto_id} onChange={(e) => setForm({ ...form, produto_id: e.target.value })} aria-invalid={!!erroDo("produto_id", erro)}>
                <option value="">Selecione…</option>
                {lista.map((p) => <option key={p.id} value={p.id}>{p.sku} — {p.nome} (saldo {p.saldo})</option>)}
              </Selecao>
            </Campo>
            <Campo rotulo="Tipo" id="tipo" erro={erroDo("tipo", erro)}>
              <Selecao id="tipo" value={form.tipo} onChange={(e) => setForm({ ...form, tipo: e.target.value as TipoMovimentacao })}>
                <option value="ENTRADA">Entrada</option>
                <option value="SAIDA">Saída</option>
                <option value="AJUSTE">Ajuste (contagem)</option>
              </Selecao>
            </Campo>
            <Campo rotulo={form.tipo === "AJUSTE" ? "Saldo contado" : "Quantidade"} id="quantidade" erro={erroDo("quantidade", erro)}>
              <Input id="quantidade" type="number" min={1} required value={form.quantidade} onChange={(e) => setForm({ ...form, quantidade: e.target.value })} aria-invalid={!!erroDo("quantidade", erro)} />
            </Campo>
            {form.tipo === "ENTRADA" ? (
              <Campo rotulo="Custo unitário (R$)" id="custo_unitario" erro={erroDo("custo_unitario", erro)}>
                <Input id="custo_unitario" type="number" step="0.01" min={0} value={form.custo_unitario} onChange={(e) => setForm({ ...form, custo_unitario: e.target.value })} aria-invalid={!!erroDo("custo_unitario", erro)} />
              </Campo>
            ) : <div />}
            <Campo rotulo="Motivo" id="motivo" erro={erroDo("motivo", erro)}>
              <Input id="motivo" value={form.motivo} onChange={(e) => setForm({ ...form, motivo: e.target.value })} />
            </Campo>
            <div className="flex items-end gap-3 md:col-span-3">
              <Button type="submit" disabled={enviando}>{enviando ? "Registrando…" : "Registrar"}</Button>
              {selecionado && <span className="text-sm text-muted-foreground">Saldo atual: {selecionado.saldo}</span>}
            </div>
          </form>
        </CardContent>
      </Card>

      <div className="grid gap-2 sm:grid-cols-4">
        <Selecao aria-label="Filtrar por tipo" value={filtros.tipo} onChange={(e) => setFiltros({ ...filtros, tipo: e.target.value, pagina: 1 })}>
          <option value="">Todos os tipos</option><option value="ENTRADA">Entrada</option><option value="SAIDA">Saída</option><option value="AJUSTE">Ajuste</option>
        </Selecao>
        <Selecao aria-label="Filtrar por produto" value={filtros.produto_id} onChange={(e) => setFiltros({ ...filtros, produto_id: e.target.value, pagina: 1 })}>
          <option value="">Todos os produtos</option>
          {lista.map((p) => <option key={p.id} value={p.id}>{p.nome}</option>)}
        </Selecao>
        <Input type="date" aria-label="De" value={filtros.de} onChange={(e) => setFiltros({ ...filtros, de: e.target.value, pagina: 1 })} />
        <Input type="date" aria-label="Até" value={filtros.ate} onChange={(e) => setFiltros({ ...filtros, ate: e.target.value, pagina: 1 })} />
      </div>
      <EstadoLista carregando={extrato.carregando} erro={extrato.erro} vazio={extrato.dados?.total === 0} mensagemVazia="Nenhuma movimentação com esses filtros." aoTentarDeNovo={extrato.recarregar}>
        {extrato.dados && (
          <>
            <div className="overflow-x-auto">
              <Table>
                <TableHeader><TableRow><TableHead>Data</TableHead><TableHead>Produto</TableHead><TableHead>Tipo</TableHead><TableHead className="text-right">Qtd.</TableHead><TableHead className="text-right">Custo</TableHead><TableHead>Motivo</TableHead></TableRow></TableHeader>
                <TableBody>
                  {extrato.dados.itens.map((m) => (
                    <TableRow key={m.id}>
                      <TableCell>{dataHora(m.criado_em)}</TableCell>
                      <TableCell>{nomeProduto(m.produto_id)}</TableCell>
                      <TableCell>{ROTULO_TIPO[m.tipo]}</TableCell>
                      <TableCell className="text-right tabular-nums">{m.quantidade}</TableCell>
                      <TableCell className="text-right tabular-nums">{m.custo_unitario ? dinheiro(m.custo_unitario) : "—"}</TableCell>
                      <TableCell>{m.motivo ?? "—"}</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
            <Paginacao pagina={extrato.dados.pagina} totalPaginas={extrato.dados.total_paginas} total={extrato.dados.total} aoMudar={(pagina) => setFiltros({ ...filtros, pagina })} />
          </>
        )}
      </EstadoLista>
    </div>
  )
}
```
Antes de fechar, conferir no back o formato aceito por `de`/`ate` (o controller diz "ISO 8601"): se `ate=2026-10-05` excluir o próprio dia (comparação com meia-noite), mandar `ate` como `${data}T23:59:59` e registrar a decisão no commit.

`src/App.tsx`: `movimentacoes` → `<Movimentacoes />`.

- [ ] **Step 2: Conferir**

Run: `npm run lint; npm run build` → sem erro.
No navegador: saída maior que o saldo → toast "Saída de N unidades excede o saldo disponível de M unidades." e campo Quantidade vermelho; entrada com custo → toast e extrato atualizado; custo some quando o tipo não é Entrada; filtros por tipo e data funcionam.

- [ ] **Step 3: Commit**

```bash
git add src
git commit -F - <<'EOF'
Cria a tela de movimentacoes com formulario e extrato filtravel

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
EOF
```

---

### Task 7: Categorias, fornecedores e usuários (F6)

**Files:**
- Create: `src/components/DialogoFormulario.tsx`, `src/pages/Categorias.tsx`, `src/pages/Fornecedores.tsx`, `src/pages/Usuarios.tsx`
- Modify: `src/App.tsx`

**Interfaces:**
- Produces: `<DialogoFormulario<T> titulo campos inicial aoEnviar(dados: T) gatilho/>` — campos `{ nome: keyof T; rotulo: string; tipo?: "text" | "email" | "password" | "select"; opcoes?: { valor: string; rotulo: string }[]; obrigatorio?: boolean }[]`. Mostra toast de erro e destaca o campo; fecha no sucesso.

- [ ] **Step 1: `src/components/DialogoFormulario.tsx`**

```tsx
import { useState, type FormEvent, type ReactNode } from "react"
import { Campo } from "@/components/Campo"
import { Selecao } from "@/components/Selecao"
import { Button } from "@/components/ui/button"
import { Dialog, DialogContent, DialogFooter, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog"
import { Input } from "@/components/ui/input"
import { erroDo, tratarErro, type ErroCampo } from "@/lib/erros"

export interface DefCampo<T> {
  nome: keyof T & string
  rotulo: string
  tipo?: "text" | "email" | "password" | "select"
  opcoes?: { valor: string; rotulo: string }[]
  obrigatorio?: boolean
}

interface Props<T extends Record<string, string>> {
  titulo: string
  campos: DefCampo<T>[]
  inicial: T
  aoEnviar: (dados: T) => Promise<void>
  gatilho: ReactNode
}

/** Diálogo de formulário simples, para os cadastros de apoio. */
export function DialogoFormulario<T extends Record<string, string>>({ titulo, campos, inicial, aoEnviar, gatilho }: Props<T>) {
  const [aberto, setAberto] = useState(false)
  const [dados, setDados] = useState<T>(inicial)
  const [erro, setErro] = useState<ErroCampo | null>(null)
  const [enviando, setEnviando] = useState(false)

  async function enviar(e: FormEvent) {
    e.preventDefault()
    setEnviando(true)
    try {
      await aoEnviar(dados)
      setAberto(false)
    } catch (falha) {
      setErro(tratarErro(falha))
    } finally {
      setEnviando(false)
    }
  }

  return (
    <Dialog open={aberto} onOpenChange={(a) => { setAberto(a); if (a) { setDados(inicial); setErro(null) } }}>
      <DialogTrigger asChild>{gatilho}</DialogTrigger>
      <DialogContent>
        <DialogHeader><DialogTitle>{titulo}</DialogTitle></DialogHeader>
        <form onSubmit={enviar} className="grid gap-3">
          {campos.map((c) => (
            <Campo key={c.nome} rotulo={c.rotulo} id={c.nome} erro={erroDo(c.nome, erro)}>
              {c.tipo === "select" ? (
                <Selecao id={c.nome} value={dados[c.nome]} onChange={(e) => setDados({ ...dados, [c.nome]: e.target.value })}>
                  {c.opcoes?.map((o) => <option key={o.valor} value={o.valor}>{o.rotulo}</option>)}
                </Selecao>
              ) : (
                <Input
                  id={c.nome} type={c.tipo ?? "text"} required={c.obrigatorio} value={dados[c.nome]}
                  aria-invalid={!!erroDo(c.nome, erro)}
                  onChange={(e) => setDados({ ...dados, [c.nome]: e.target.value })}
                />
              )}
            </Campo>
          ))}
          <DialogFooter><Button type="submit" disabled={enviando}>{enviando ? "Salvando…" : "Salvar"}</Button></DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  )
}
```

- [ ] **Step 2: `src/pages/Categorias.tsx`**

```tsx
import { useState } from "react"
import { toast } from "sonner"
import { api } from "@/api/cliente"
import type { Categoria, Pagina } from "@/api/tipos"
import { ConfirmarAcao } from "@/components/ConfirmarAcao"
import { DialogoFormulario } from "@/components/DialogoFormulario"
import { EstadoLista } from "@/components/EstadoLista"
import { Paginacao } from "@/components/Paginacao"
import { Button } from "@/components/ui/button"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { useConsulta } from "@/hooks/useConsulta"
import { tratarErro } from "@/lib/erros"

const CAMPOS = [{ nome: "nome" as const, rotulo: "Nome", obrigatorio: true }]

export default function Categorias() {
  const [pagina, setPagina] = useState(1)
  const lista = useConsulta(() => api.get<Pagina<Categoria>>("/categorias", { pagina, por_pagina: 20 }), [pagina])

  async function excluir(c: Categoria) {
    try {
      await api.delete(`/categorias/${c.id}`)
      toast.success("Categoria excluída.")
      lista.recarregar()
    } catch (e) {
      tratarErro(e)
    }
  }

  return (
    <div className="grid gap-4">
      <div className="flex items-center justify-between gap-2">
        <h1 className="text-2xl font-semibold">Categorias</h1>
        <DialogoFormulario
          titulo="Nova categoria" campos={CAMPOS} inicial={{ nome: "" }}
          aoEnviar={async (d) => { await api.post("/categorias", d); toast.success("Categoria criada."); lista.recarregar() }}
          gatilho={<Button>Nova categoria</Button>}
        />
      </div>
      <EstadoLista carregando={lista.carregando} erro={lista.erro} vazio={lista.dados?.total === 0} mensagemVazia="Nenhuma categoria cadastrada." aoTentarDeNovo={lista.recarregar}>
        {lista.dados && (
          <>
            <Table>
              <TableHeader><TableRow><TableHead>Nome</TableHead><TableHead className="w-48">Ações</TableHead></TableRow></TableHeader>
              <TableBody>
                {lista.dados.itens.map((c) => (
                  <TableRow key={c.id}>
                    <TableCell>{c.nome}</TableCell>
                    <TableCell className="flex gap-1">
                      <DialogoFormulario
                        titulo="Editar categoria" campos={CAMPOS} inicial={{ nome: c.nome }}
                        aoEnviar={async (d) => { await api.put(`/categorias/${c.id}`, d); toast.success("Categoria atualizada."); lista.recarregar() }}
                        gatilho={<Button size="sm" variant="outline">Editar</Button>}
                      />
                      <ConfirmarAcao titulo={`Excluir ${c.nome}?`} descricao="Só é possível excluir categoria sem produtos." rotulo="Excluir" aoConfirmar={() => excluir(c)} gatilho={<Button size="sm" variant="ghost">Excluir</Button>} />
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
            <Paginacao pagina={lista.dados.pagina} totalPaginas={lista.dados.total_paginas} total={lista.dados.total} aoMudar={setPagina} />
          </>
        )}
      </EstadoLista>
    </div>
  )
}
```

- [ ] **Step 3: `src/pages/Fornecedores.tsx`**

```tsx
import { useState } from "react"
import { toast } from "sonner"
import { api } from "@/api/cliente"
import type { Fornecedor, Pagina } from "@/api/tipos"
import { ConfirmarAcao } from "@/components/ConfirmarAcao"
import { DialogoFormulario, type DefCampo } from "@/components/DialogoFormulario"
import { EstadoLista } from "@/components/EstadoLista"
import { Paginacao } from "@/components/Paginacao"
import { Button } from "@/components/ui/button"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { useConsulta } from "@/hooks/useConsulta"
import { tratarErro } from "@/lib/erros"

type Form = { nome: string; cnpj: string; email: string; telefone: string }
const CAMPOS: DefCampo<Form>[] = [
  { nome: "nome", rotulo: "Nome", obrigatorio: true },
  { nome: "cnpj", rotulo: "CNPJ" },
  { nome: "email", rotulo: "E-mail", tipo: "email" },
  { nome: "telefone", rotulo: "Telefone" },
]
const corpo = (d: Form) => ({ nome: d.nome, cnpj: d.cnpj || null, email: d.email || null, telefone: d.telefone || null })

export default function Fornecedores() {
  const [pagina, setPagina] = useState(1)
  const lista = useConsulta(() => api.get<Pagina<Fornecedor>>("/fornecedores", { pagina, por_pagina: 20 }), [pagina])

  async function excluir(f: Fornecedor) {
    try {
      await api.delete(`/fornecedores/${f.id}`)
      toast.success("Fornecedor excluído.")
      lista.recarregar()
    } catch (e) {
      tratarErro(e)
    }
  }

  return (
    <div className="grid gap-4">
      <div className="flex items-center justify-between gap-2">
        <h1 className="text-2xl font-semibold">Fornecedores</h1>
        <DialogoFormulario
          titulo="Novo fornecedor" campos={CAMPOS} inicial={{ nome: "", cnpj: "", email: "", telefone: "" }}
          aoEnviar={async (d) => { await api.post("/fornecedores", corpo(d)); toast.success("Fornecedor criado."); lista.recarregar() }}
          gatilho={<Button>Novo fornecedor</Button>}
        />
      </div>
      <EstadoLista carregando={lista.carregando} erro={lista.erro} vazio={lista.dados?.total === 0} mensagemVazia="Nenhum fornecedor cadastrado." aoTentarDeNovo={lista.recarregar}>
        {lista.dados && (
          <>
            <div className="overflow-x-auto">
              <Table>
                <TableHeader><TableRow><TableHead>Nome</TableHead><TableHead>CNPJ</TableHead><TableHead>E-mail</TableHead><TableHead>Telefone</TableHead><TableHead>Ações</TableHead></TableRow></TableHeader>
                <TableBody>
                  {lista.dados.itens.map((f) => (
                    <TableRow key={f.id}>
                      <TableCell>{f.nome}</TableCell>
                      <TableCell>{f.cnpj ?? "—"}</TableCell>
                      <TableCell>{f.email ?? "—"}</TableCell>
                      <TableCell>{f.telefone ?? "—"}</TableCell>
                      <TableCell className="flex gap-1">
                        <DialogoFormulario
                          titulo="Editar fornecedor" campos={CAMPOS}
                          inicial={{ nome: f.nome, cnpj: f.cnpj ?? "", email: f.email ?? "", telefone: f.telefone ?? "" }}
                          aoEnviar={async (d) => { await api.put(`/fornecedores/${f.id}`, corpo(d)); toast.success("Fornecedor atualizado."); lista.recarregar() }}
                          gatilho={<Button size="sm" variant="outline">Editar</Button>}
                        />
                        <ConfirmarAcao titulo={`Excluir ${f.nome}?`} descricao="Só é possível excluir fornecedor sem produtos." rotulo="Excluir" aoConfirmar={() => excluir(f)} gatilho={<Button size="sm" variant="ghost">Excluir</Button>} />
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
            <Paginacao pagina={lista.dados.pagina} totalPaginas={lista.dados.total_paginas} total={lista.dados.total} aoMudar={setPagina} />
          </>
        )}
      </EstadoLista>
    </div>
  )
}
```

- [ ] **Step 4: `src/pages/Usuarios.tsx`**

```tsx
import { useState } from "react"
import { toast } from "sonner"
import { api } from "@/api/cliente"
import type { Pagina, Usuario } from "@/api/tipos"
import { useSessao } from "@/auth/AuthContext"
import { ConfirmarAcao } from "@/components/ConfirmarAcao"
import { DialogoFormulario, type DefCampo } from "@/components/DialogoFormulario"
import { EstadoLista } from "@/components/EstadoLista"
import { Paginacao } from "@/components/Paginacao"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { useConsulta } from "@/hooks/useConsulta"
import { tratarErro } from "@/lib/erros"

type Form = { nome: string; email: string; senha: string; role: string }
const PAPEIS = [{ valor: "OPERADOR", rotulo: "Operador" }, { valor: "ADMIN", rotulo: "Administrador" }]
const NOVO: DefCampo<Form>[] = [
  { nome: "nome", rotulo: "Nome", obrigatorio: true },
  { nome: "email", rotulo: "E-mail", tipo: "email", obrigatorio: true },
  { nome: "senha", rotulo: "Senha", tipo: "password", obrigatorio: true },
  { nome: "role", rotulo: "Papel", tipo: "select", opcoes: PAPEIS },
]
const EDICAO: DefCampo<Form>[] = NOVO.map((c) => (c.nome === "senha" ? { ...c, rotulo: "Nova senha (opcional)", obrigatorio: false } : c))

export default function Usuarios() {
  const { usuario: eu } = useSessao()
  const [pagina, setPagina] = useState(1)
  const lista = useConsulta(() => api.get<Pagina<Usuario>>("/usuarios", { pagina, por_pagina: 20, incluir_inativos: true }), [pagina])

  async function desativar(u: Usuario) {
    try {
      await api.delete(`/usuarios/${u.id}`)
      toast.success(`${u.nome} desativado.`)
      lista.recarregar()
    } catch (e) {
      tratarErro(e)
    }
  }

  return (
    <div className="grid gap-4">
      <div className="flex items-center justify-between gap-2">
        <h1 className="text-2xl font-semibold">Usuários</h1>
        <DialogoFormulario
          titulo="Novo usuário" campos={NOVO} inicial={{ nome: "", email: "", senha: "", role: "OPERADOR" }}
          aoEnviar={async (d) => { await api.post("/usuarios", d); toast.success("Usuário criado."); lista.recarregar() }}
          gatilho={<Button>Novo usuário</Button>}
        />
      </div>
      <EstadoLista carregando={lista.carregando} erro={lista.erro} vazio={lista.dados?.total === 0} mensagemVazia="Nenhum usuário." aoTentarDeNovo={lista.recarregar}>
        {lista.dados && (
          <>
            <div className="overflow-x-auto">
              <Table>
                <TableHeader><TableRow><TableHead>Nome</TableHead><TableHead>E-mail</TableHead><TableHead>Papel</TableHead><TableHead>Situação</TableHead><TableHead>Ações</TableHead></TableRow></TableHeader>
                <TableBody>
                  {lista.dados.itens.map((u) => (
                    <TableRow key={u.id}>
                      <TableCell>{u.nome}</TableCell>
                      <TableCell>{u.email}</TableCell>
                      <TableCell>{u.role === "ADMIN" ? "Administrador" : "Operador"}</TableCell>
                      <TableCell>{u.ativo ? <Badge variant="secondary">ativo</Badge> : <Badge variant="outline">inativo</Badge>}</TableCell>
                      <TableCell className="flex gap-1">
                        <DialogoFormulario
                          titulo="Editar usuário" campos={EDICAO} inicial={{ nome: u.nome, email: u.email, senha: "", role: u.role }}
                          aoEnviar={async (d) => {
                            const { senha, ...resto } = d
                            await api.put(`/usuarios/${u.id}`, senha ? d : resto)
                            toast.success("Usuário atualizado.")
                            lista.recarregar()
                          }}
                          gatilho={<Button size="sm" variant="outline">Editar</Button>}
                        />
                        {u.ativo && u.id !== eu?.id && (
                          <ConfirmarAcao titulo={`Desativar ${u.nome}?`} descricao="A pessoa perde o acesso na hora; o histórico é mantido." rotulo="Desativar" aoConfirmar={() => desativar(u)} gatilho={<Button size="sm" variant="ghost">Desativar</Button>} />
                        )}
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
            <Paginacao pagina={lista.dados.pagina} totalPaginas={lista.dados.total_paginas} total={lista.dados.total} aoMudar={setPagina} />
          </>
        )}
      </EstadoLista>
    </div>
  )
}
```

`src/App.tsx`: trocar os três `EmBreve` restantes e apagar a função `EmBreve`.

- [ ] **Step 2: Conferir**

Run: `npm test; npm run lint; npm run build` → sem erro.
No navegador (admin): criar categoria "Padaria" → toast; excluir categoria com produtos → toast com a mensagem do back; fornecedor com CNPJ repetido → campo CNPJ vermelho; criar operador e desativá-lo; rebaixar o último admin → toast com o erro do campo `role`.

- [ ] **Step 3: Commit**

```bash
git add src
git commit -F - <<'EOF'
Cria as telas de categorias, fornecedores e usuarios

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
EOF
```

---

### Task 8: E2E com pytest-playwright (F8)

Roda pelo Claude (o sandbox do Codex bloqueia o Playwright no Windows).

**Files:**
- Create: `e2e/requirements.txt`, `e2e/conftest.py`, `e2e/test_fluxos.py`, `e2e/README.md`, `pytest.ini` (na raiz do front)

**Interfaces:**
- Consumes: textos e `data-testid` das Tasks 3–6: botão "Entrar", rótulos "E-mail"/"Senha", heading "Dashboard", `kpi-em_ruptura`, botão "Novo produto", rótulos "SKU", "Nome", "Categoria", botão "Salvar", página Movimentações com "Produto", "Tipo", "Quantidade", "Registrar", botão "Abrir menu".

- [ ] **Step 1: Ambiente**

`e2e/requirements.txt`:
```
pytest==9.1.1
pytest-playwright==0.7.2
```
Antes de fixar, conferir a versão com `python -m pip index versions pytest-playwright` e usar a mais nova.

`pytest.ini` (raiz do front):
```ini
[pytest]
testpaths = e2e
```
Instalar:
```powershell
python -m venv e2e\.venv
e2e\.venv\Scripts\python.exe -m pip install -r e2e\requirements.txt
e2e\.venv\Scripts\python.exe -m playwright install chromium
```

- [ ] **Step 2: `e2e/conftest.py`**

```python
"""E2E contra back e front locais.

Pré-requisitos (ver e2e/README.md): back com `seed.py --recriar` rodando em
:5000 e `npm run dev` em :5173.
"""

import os

import pytest
from playwright.sync_api import Page, expect

URL_FRONT = os.getenv("E2E_URL_FRONT", "http://localhost:5173")


@pytest.fixture(scope="session")
def browser_context_args(browser_context_args):
    return {**browser_context_args, "base_url": URL_FRONT, "locale": "pt-BR"}


def entrar(page: Page, email: str, senha: str) -> None:
    page.goto("/login")
    page.get_by_label("E-mail").fill(email)
    page.get_by_label("Senha").fill(senha)
    page.get_by_role("button", name="Entrar").click()
    expect(page.get_by_role("heading", name="Dashboard")).to_be_visible()


@pytest.fixture
def admin(page: Page) -> Page:
    entrar(page, "admin@demo.com", "admin123")
    return page
```

- [ ] **Step 3: `e2e/test_fluxos.py`**

```python
import time

from playwright.sync_api import Page, expect

from conftest import entrar


def _sku() -> str:
    return f"E2E-{int(time.time() * 1000)}"


def test_login_leva_ao_dashboard(admin: Page):
    expect(admin.get_by_role("link", name="Usuários")).to_be_visible()


def test_dashboard_mostra_numeros_do_seed(admin: Page):
    expect(admin.get_by_test_id("kpi-em_ruptura")).to_contain_text("3")
    expect(admin.get_by_test_id("kpi-produtos_ativos")).not_to_contain_text("0")
    expect(admin.get_by_text("Entradas × saídas por dia")).to_be_visible()


def _criar_produto(page: Page, sku: str) -> None:
    page.get_by_role("link", name="Produtos").click()
    page.get_by_role("button", name="Novo produto").click()
    page.get_by_label("SKU").fill(sku)
    page.get_by_label("Nome").fill(f"Produto {sku}")
    page.get_by_label("Categoria").select_option(index=1)
    page.get_by_role("button", name="Salvar").click()
    expect(page.get_by_text("Produto criado.")).to_be_visible()


def test_criar_produto(admin: Page):
    sku = _sku()
    _criar_produto(admin, sku)
    expect(admin.get_by_role("cell", name=sku)).to_be_visible()


def test_saida_acima_do_saldo_mostra_rn02(admin: Page):
    sku = _sku()
    _criar_produto(admin, sku)
    admin.get_by_role("link", name="Movimentações").click()
    admin.get_by_label("Produto").select_option(label=f"{sku} — Produto {sku} (saldo 0)")
    admin.get_by_label("Tipo").select_option("SAIDA")
    admin.get_by_label("Quantidade").fill("5")
    admin.get_by_role("button", name="Registrar").click()
    expect(admin.get_by_text("excede o saldo disponível de 0 unidades").first).to_be_visible()


def test_operador_nao_ve_usuarios(page: Page):
    entrar(page, "operador@demo.com", "operador123")
    expect(page.get_by_role("link", name="Produtos")).to_be_visible()
    expect(page.get_by_role("link", name="Usuários")).to_have_count(0)
    page.goto("/usuarios")
    expect(page.get_by_role("heading", name="Dashboard")).to_be_visible()


def test_celular_abre_menu_em_gaveta(page: Page):
    page.set_viewport_size({"width": 390, "height": 844})
    entrar(page, "admin@demo.com", "admin123")
    page.get_by_role("button", name="Abrir menu").click()
    page.get_by_role("dialog").get_by_role("link", name="Produtos").click()
    expect(page.get_by_role("heading", name="Produtos")).to_be_visible()
```
`from conftest import entrar` funciona porque o pytest põe `e2e/` no `sys.path` (rootdir sem `__init__.py`).

- [ ] **Step 4: Rodar**

Em três terminais (o 1 e o 2 com `Start-Process`, em janela própria, para não caírem):
1. `C:\dev\cp-python\backend`: `.venv\Scripts\python.exe seed.py --recriar; .venv\Scripts\python.exe app.py`
2. `C:\dev\cp-python\frontend`: `npm run dev`
3. `C:\dev\cp-python\frontend`: `e2e\.venv\Scripts\python.exe -m pytest -q`

Expected: `6 passed`. Se algum falhar, `superpowers:systematic-debugging` (rodar com `--headed` ou `--tracing on` para ver). Locator que não casa com o texto real da tela é bug do teste ou da tela: decidir qual e registrar.

- [ ] **Step 5: `e2e/README.md`**

```markdown
# E2E (pytest-playwright)

Seis fluxos: login, números do dashboard, criar produto, saída acima do saldo (RN-02),
operador sem menu de usuários e menu em gaveta no celular.

```powershell
# uma vez
python -m venv e2e\.venv
e2e\.venv\Scripts\python.exe -m pip install -r e2e\requirements.txt
e2e\.venv\Scripts\python.exe -m playwright install chromium

# a cada rodada: back com seed novo em :5000 e front em :5173, depois
e2e\.venv\Scripts\python.exe -m pytest -q
```

O teste de números espera o seed recém-criado (`seed.py --recriar`): 3 produtos em ruptura.
```
No README do front, seção "Checagens", acrescentar: "E2E: ver `e2e/README.md`."

- [ ] **Step 6: Commit**

```bash
git add e2e/requirements.txt e2e/conftest.py e2e/test_fluxos.py e2e/README.md pytest.ini README.md
git commit -F - <<'EOF'
Adiciona seis fluxos E2E com pytest-playwright

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
EOF
```

---

### Task 9: Verificação final e docs

- [ ] **Step 1: Critérios da SPEC (`superpowers:verification-before-completion`)**

1. `npm run lint; npm run build; npm test` → sem erro (critério 7).
2. E2E → `6 passed` (critério 7).
3. `git grep -n "dangerouslySetInnerHTML"` → nada (critério 8).
4. `git status`/`git ls-files` sem `.env`, `node_modules`, `e2e/.venv` (critério 8).
5. Dashboard faz só `GET /dashboard/resumo` e `GET /relatorios/reposicao/ultimo` (critério 4) — conferido na Task 4.

- [ ] **Step 2: Docs**

- `README.md` do front: seção "Telas" com uma linha por rota (`/login`, `/cadastro`, `/`, `/produtos`, `/produtos/:id`, `/movimentacoes`, `/categorias`, `/fornecedores` e `/usuarios` só ADMIN) e seção "Integração com a API" (cliente único em `src/api/cliente.ts`, token no `localStorage`, logout no 401, envelope de erro → toast + campo destacado).
- `CLAUDE.md` do front, "Como trabalhar aqui": trocar a linha "Plano do front ainda não existe…" por "Plano do front: `../backend/docs/superpowers/plans/2026-10-05-cp2-frontend.md`."

- [ ] **Step 3: Commit**

```bash
git add README.md CLAUDE.md
git commit -F - <<'EOF'
Documenta telas e integracao do front com a API

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
EOF
```
**Não fazer push** — pedir o ok do Felipe.

---

## Self-review (feito ao escrever)

- **Cobertura da SPEC:** F1 → Task 1 (+ cliente na 2); F2 → Task 3; F3 → Task 4; F4 → Task 5; F5 → Task 6; F6 → Task 7; F7 → `tratarErro`, `Campo`, `EstadoLista` (Task 3) usados em todas as telas; F8 → Task 8. Critérios 4, 7 e 8 → Task 9.
- **Testes automatizados no front:** Vitest só no que tem lógica (cliente, formatação, menu por papel: 11 testes); telas são cobertas pelos 6 E2E. Escolha deliberada pelo prazo.
- **Desvios deliberados:** select nativo (`Selecao`) em vez do Select do shadcn — mais simples e testável com `select_option`; `useCatalogo` e o select de produto da Task 6 carregam no máximo 100 itens (limite da API), suficiente para a demo.
- **Riscos conhecidos de API de biblioteca** (conferir na execução, não no plano): flags do `shadcn init`, regra `react-refresh/only-export-components` no `AuthContext` e no `ROTULO_TIPO`, fechamento da gaveta ao navegar. Cada um tem a saída descrita no passo.
