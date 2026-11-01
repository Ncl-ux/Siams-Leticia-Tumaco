"""Valida un CSV de datos de campo (app offline XUE Hub) contra config/esquema_datos_campo.csv.

Uso: python scripts/validar_datos_campo.py archivo.csv   (código de salida 1 si hay errores)
"""
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from siams.datos_campo import validar  # noqa: E402

if __name__ == "__main__":
    df = pd.read_csv(sys.argv[1], dtype=str, encoding="utf-8-sig")
    errores = validar(df)
    for e in errores:
        print(e)
    print("OK" if not errores else f"{len(errores)} error(es)")
    sys.exit(1 if errores else 0)
