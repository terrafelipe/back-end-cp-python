# Como testar tudo, do zero

## 0. Pré-requisitos e setup (uma vez por máquina, ~3 min)

Python 3.12 ou superior (`python --version`). Nenhum `.env` é necessário.

```powershell
cd C:\dev\cp-python\backend
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe seed.py
```

## 1. Testes automatizados

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt   # uma vez
.\.venv\Scripts\python.exe -m pytest -q
```

Banco SQLite em memória, recriado a cada teste; nenhum teste acessa a rede.

## 2. Subir localmente e conferir (~2 min)

```powershell
.\.venv\Scripts\python.exe app.py
```

- `http://127.0.0.1:5000/health` → `{"status": "ok", "banco": "conectado"}`
- `http://127.0.0.1:5000/swagger` → rotas agrupadas por recurso
- `POST /auth/login` com `admin@demo.com` / `admin123` → `access_token`; em **Authorize**, `Bearer <token>`
- `GET /estoque/alertas` → 3 produtos em ruptura (dados do seed)
- `GET /dashboard/resumo?dias=30` → série com 30 dias preenchidos

## 5. Cenários de negócio

O roteiro de 11 passos está no `README.md`, seção "Roteiro de validação" (saída acima do saldo → 422
RN-02; editar movimentação → 405 RN-04; operador excluindo produto → 403 RN-10; outra empresa → 404).

## Se algo falhar

| Sintoma | Causa provável | Correção |
|---|---|---|
| `No module named flask` | rodou o `python` global | usar `.\.venv\Scripts\python.exe` |
| 401 em tudo no Swagger | token sem o prefixo | informar `Bearer <token>` no Authorize |
| Seed diz "dados já existem" | a empresa demo já está no banco | `.\.venv\Scripts\python.exe seed.py --recriar` |
| Acentos quebrados ao ler `.env.example` | PowerShell 5.1 lê como ANSI | `Get-Content -Encoding UTF8` |
