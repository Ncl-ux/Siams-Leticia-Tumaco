#!/usr/bin/env python
"""Aplica los criterios de config/landsat_criterios.toml a las escenas Landsat de cada sede.

Para cada carpeta ``Landsat/<Sede>/``:

1. Lee ``Control_escenas.csv`` (registro exportado desde Colab: fecha, nubosidad del catálogo,
   estado, fracción útil del buffer e identificador de escena) y escribe
   ``metadatos_escenas.csv`` con sensor, path/row, tier, nubosidad sobre el AOI, cumplimiento y
   motivos de rechazo de cada escena.
2. Si existe el GIF original (``GIF_Landsat_*.gif``), extrae SOLO los fotogramas de escenas que
   cumplen a ``escenas/<id_escena>.png``. Los GIF de Colab tienen un fotograma por escena
   aceptada, en el mismo orden de las filas aceptadas del CSV (verificado con la fecha impresa
   en cada fotograma).
3. Con ``--eliminar-gif`` borra el GIF, que mezcla escenas que cumplen y que no cumplen.

Uso, desde la raíz del repositorio:

    python scripts/07_landsat_filtrar_escenas.py [--eliminar-gif]

Para recuperar un GIF ya borrado: ``git show 5e38ec4:"Landsat/Leticia/GIF_Landsat_Leticia_2025.gif" > x.gif``.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))
from siams.landsat import cargar_criterios, evaluar_control_escenas, nombre_imagen_escena  # noqa: E402

CARPETA = RAIZ / "Landsat"
# Carpeta del repositorio → nombre de la sede en la app (TERRITORIOS).
SEDES = {"Arauca": "Arauca", "La Paz": "La Paz", "Leticia": "Leticia", "Medellin": "Medellín",
         "San Andres": "San Andrés", "Tumaco": "Tumaco"}


def extraer_fotogramas(gif: Path, tabla: pd.DataFrame, destino: Path) -> int:
    from PIL import Image

    cumplen = tabla[tabla["cumple"] & tabla["fotograma_gif"].notna()]
    if not cumplen.empty:
        destino.mkdir(exist_ok=True)
    with Image.open(gif) as im:
        n = im.n_frames
        aceptadas = int(tabla["fotograma_gif"].notna().sum())
        if n != aceptadas:
            raise SystemExit(f"{gif}: {n} fotogramas pero {aceptadas} escenas aceptadas; no se puede emparejar.")
        for _, r in cumplen.iterrows():
            im.seek(int(r["fotograma_gif"]))
            # Paleta adaptativa sin tramado: conserva los colores de clase y reduce el peso.
            img = im.convert("RGB").quantize(colors=64, dither=0)
            img.save(destino / nombre_imagen_escena(r["id_escena"]), optimize=True)
    return len(cumplen)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--eliminar-gif", action="store_true", help="borra el GIF original después de extraer")
    a = ap.parse_args(argv)
    criterios = cargar_criterios()
    for carpeta, sede in SEDES.items():
        d = CARPETA / carpeta
        control = d / "Control_escenas.csv"
        if not control.exists():
            print(f"{sede}: sin Control_escenas.csv")
            continue
        tabla = evaluar_control_escenas(pd.read_csv(control), sede, criterios)
        tabla.to_csv(d / "metadatos_escenas.csv", index=False, date_format="%Y-%m-%d")
        gifs = sorted(d.glob("GIF_Landsat_*.gif"))
        n_img = 0
        for gif in gifs:
            n_img += extraer_fotogramas(gif, tabla, d / "escenas")
            if a.eliminar_gif:
                gif.unlink()
        print(f"{sede}: {len(tabla)} escenas, {int(tabla['cumple'].sum())} cumplen; "
              f"{n_img} imágenes extraídas{' y GIF eliminado' if gifs and a.eliminar_gif else ''}")


if __name__ == "__main__":
    main()
