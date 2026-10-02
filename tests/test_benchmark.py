"""O benchmark roda em subprocesso: ele cria a própria app (ver conftest)."""

import os
import subprocess
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent


def test_benchmark_roda_com_volume_pequeno():
    resultado = subprocess.run(
        [sys.executable, "scripts/benchmark.py", "--produtos", "20",
         "--movimentacoes", "300", "--repeticoes", "2"],
        cwd=RAIZ,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=120,
        env={**os.environ, "PYTHONIOENCODING": "utf-8"},
    )
    assert resultado.returncode == 0, resultado.stderr
    assert "| `/estoque/alertas` |" in resultado.stdout
