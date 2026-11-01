"""Tendencias (Mann-Kendall, Hamed-Rao, Sen) y homogeneidad (Pettitt, SNHT) por sede.

Lee los CSV de ``scripts/02_agregados_anuales.py`` y escribe
``docs/tendencias_homogeneidad.csv``. Para series con inhomogeneidad
documentada (``siams/calidad.py``) agrega una fila con el tramo homogéneo.

Uso:
    python scripts/02_agregados_anuales.py
    python scripts/03_tendencias_homogeneidad.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))

from siams.calidad import SERIES_INHOMOGENEAS  # noqa: E402
from siams.estadistica import (  # noqa: E402
    evaluar_homogeneidad, mann_kendall, mann_kendall_hamed_rao, pendiente_sen,
)

ENTRADA = RAIZ / "data" / "processed" / "anuales"
SALIDA = RAIZ / "docs" / "tendencias_homogeneidad.csv"

NOMBRE_VARIABLE = {"precipitacion": "Precipitación"}
NOMBRE_SEDE = {"tumaco": "Tumaco", "leticia": "Leticia", "arauca": "Arauca", "lapaz": "La Paz",
               "medellin": "Medellín", "san_andres": "San Andrés"}


def fila(sede, fuente, variable, unidad, g, nota=""):
    mk = mann_kendall(g["valor"])
    hr = mann_kendall_hamed_rao(g["valor"])
    sen = pendiente_sen(g["anio"], g["valor"])
    h = evaluar_homogeneidad(g["anio"], g["valor"]) if len(g) >= 10 else {}
    return {
        "sede": sede, "fuente": fuente, "variable": variable, "unidad_anual": unidad,
        "periodo": f"{g['anio'].min()}-{g['anio'].max()}", "n_anios": len(g),
        "tau": round(mk["tau"], 3), "p_mk": round(mk["p"], 5), "p_hamed_rao": round(hr["p"], 5),
        "sen_por_anio": round(sen["pendiente"], 4), "tendencia_mk": mk["tendencia"],
        "pettitt_p": round(h.get("pettitt_p", float("nan")), 5),
        "snht_p": round(h.get("snht_p", float("nan")), 5),
        "anio_cambio_pettitt": h.get("anio_cambio"), "dictamen_homogeneidad": h.get("dictamen", "n<10"),
        "nota": nota,
    }


def main() -> None:
    filas = []
    for csv in sorted(ENTRADA.glob("*_anual.csv")):
        fuente_txt, sede_txt = csv.stem.replace("_anual", "").split("_", 1) if csv.stem.startswith("ideam") \
            else ("nasa_power", csv.stem.replace("nasa_power_", "").replace("_anual", ""))
        fuente = "IDEAM" if fuente_txt == "ideam" else "NASA POWER"
        sede = NOMBRE_SEDE.get(sede_txt, sede_txt)
        df = pd.read_csv(csv)
        for (variable, unidad), g in df.groupby(["variable", "unidad"]):
            g = g.sort_values("anio")
            if len(g) < 5:
                continue
            nombre = NOMBRE_VARIABLE.get(variable, variable)
            marca = SERIES_INHOMOGENEAS.get((sede, fuente, nombre))
            filas.append(fila(sede, fuente, variable, unidad, g,
                              "INHOMOGÉNEA DOCUMENTADA: tendencia no concluyente" if marca else ""))
            if marca:
                ini, fin = marca["tramo_homogeneo"]
                filas.append(fila(sede, fuente, variable, unidad,
                                  g[(g["anio"] >= ini) & (g["anio"] <= fin)],
                                  f"Tramo homogéneo {ini}-{fin}"))
    SALIDA.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(filas).to_csv(SALIDA, index=False, encoding="utf-8")
    print(f"Escrito {SALIDA.relative_to(RAIZ)} ({len(filas)} filas)")


if __name__ == "__main__":
    main()
