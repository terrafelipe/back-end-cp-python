import json
import os
import subprocess
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent


def test_duas_saidas_simultaneas_do_saldo_inteiro_so_uma_passa(tmp_path):
    saida = subprocess.run(
        [sys.executable, str(RAIZ / "tests" / "_corrida_saida.py"), str(tmp_path / "corrida.db")],
        cwd=RAIZ, env={**os.environ, "PYTHONPATH": str(RAIZ)}, capture_output=True, text=True, timeout=60, check=True,
    )
    resultado = json.loads(saida.stdout.strip().splitlines()[-1])
    assert resultado["resultados"] == ["RN-02", "ok"]
    assert resultado["cache"] == resultado["historico"] == 0
