"""Criterios de calidad para escenas y compuestos Landsat (sin dependencias de Streamlit).

Lo usan la app, ``scripts/07_landsat_filtrar_escenas.py`` y las pruebas. Los umbrales viven en
``config/landsat_criterios.toml``.
"""

from __future__ import annotations

import re
import tomllib
import unicodedata
from pathlib import Path

import pandas as pd

RAIZ = Path(__file__).resolve().parents[1]
RUTA_CRITERIOS = RAIZ / "config" / "landsat_criterios.toml"

SENSORES = {
    "LT04": "Landsat 4 TM",
    "LT05": "Landsat 5 TM",
    "LE07": "Landsat 7 ETM+",
    "LC08": "Landsat 8 OLI/TIRS",
    "LC09": "Landsat 9 OLI-2/TIRS-2",
}

# LC09_L2SP_006055_20241208_02_T1 (índice de GEE) o
# LC09_L2SP_006055_20241208_20241210_02_T1 (identificador completo de USGS).
_PATRON_ID = re.compile(
    r"^(?P<sensor>L[CEOT]0\d)_(?P<nivel>L\d[A-Z]{2})_(?P<path>\d{3})(?P<row>\d{3})_"
    r"(?P<adquisicion>\d{8})(?:_(?P<proceso>\d{8}))?_(?P<coleccion>\d{2})_(?P<tier>T1|T2|RT)$"
)


def normalizar(texto: str) -> str:
    base = unicodedata.normalize("NFKD", str(texto))
    return "".join(c for c in base if not unicodedata.combining(c)).casefold().strip()


def cargar_criterios(ruta: Path | str | None = None) -> dict:
    with open(ruta or RUTA_CRITERIOS, "rb") as f:
        criterios = tomllib.load(f)
    for seccion in ("ventana_estacional", "buffer_km"):
        criterios[seccion] = {normalizar(k): v for k, v in criterios.get(seccion, {}).items()}
    return criterios


def analizar_id_escena(id_escena: str) -> dict | None:
    """Descompone el identificador Landsat Collection 2. Devuelve None si no se reconoce."""
    m = _PATRON_ID.match(str(id_escena).strip())
    if not m:
        return None
    d = m.groupdict()
    return {
        "sensor": d["sensor"],
        "sensor_nombre": SENSORES.get(d["sensor"], d["sensor"]),
        "nivel": d["nivel"],
        "path_row": f"{d['path']}/{d['row']}",
        "fecha_adquisicion": pd.Timestamp(d["adquisicion"]),
        "coleccion": d["coleccion"],
        "tier": d["tier"],
    }


def motivos_incumplimiento(escena: dict, sede: str, criterios: dict) -> list[str]:
    """Lista de criterios que la escena no cumple (vacía si cumple todos).

    ``escena`` necesita: id, fecha (opcional si el id trae la fecha), nube_aoi_pct y estado_original.
    """
    g = criterios["general"]
    motivos = []
    meta = analizar_id_escena(escena.get("id", ""))
    if meta is None:
        return ["identificador de escena no reconocido"]
    fecha = pd.to_datetime(escena.get("fecha") or meta["fecha_adquisicion"], errors="coerce")
    if pd.isna(fecha):
        fecha = meta["fecha_adquisicion"]

    estado = normalizar(escena.get("estado_original", "aceptada"))
    if estado and not estado.startswith("aceptad"):
        motivos.append("descartada en el procesamiento original")
    if meta["coleccion"] != g.get("coleccion", "02"):
        motivos.append(f"colección {meta['coleccion']} (se exige {g.get('coleccion', '02')})")
    if meta["nivel"] not in g.get("niveles_permitidos", ["L2SP"]):
        motivos.append(f"nivel {meta['nivel']} (no es reflectancia superficial L2SP)")
    if meta["tier"] not in g.get("tiers_permitidos", ["T1"]):
        motivos.append(f"{meta['tier']} (se exige Tier 1: geometría y calibración de mejor calidad)")
    if meta["sensor"] not in g.get("sensores_permitidos", []):
        motivos.append(f"sensor {meta['sensor']} no permitido")
    elif meta["sensor"] == "LE07" and fecha >= pd.Timestamp(g.get("le07_slc_off_desde", "2003-05-31")):
        motivos.append("Landsat 7 con SLC apagado (franjas sin dato)")

    if g.get("exigir_ventana_estacional", True):
        meses = criterios["ventana_estacional"].get(normalizar(sede))
        if meses is None:
            motivos.append("la sede no tiene ventana estacional definida")
        elif int(fecha.month) not in meses:
            motivos.append(f"fuera de la ventana estacional ({_texto_meses(meses)})")

    nube = pd.to_numeric(escena.get("nube_aoi_pct"), errors="coerce")
    if pd.isna(nube):
        motivos.append("sin nubosidad calculada sobre el AOI")
    elif float(nube) > float(g["nube_aoi_max_pct"]):
        motivos.append(f"AOI sin dato útil {float(nube):.0f} % > {float(g['nube_aoi_max_pct']):g} %")
    return motivos


def _texto_meses(meses) -> str:
    nombres = ["ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic"]
    return ", ".join(nombres[m - 1] for m in meses)


def evaluar_control_escenas(control: pd.DataFrame, sede: str, criterios: dict) -> pd.DataFrame:
    """Tabla de metadatos y cumplimiento a partir de Control_escenas.csv.

    Columnas de entrada esperadas: fecha, nubosidad_catalogo, estado, fraccion_util, id.
    ``fotograma`` es la posición de la escena en el GIF original: los GIF exportados desde
    Colab tienen un fotograma por escena aceptada, en el orden de las filas aceptadas.
    """
    filas = []
    n_aceptada = 0
    for _, r in control.iterrows():
        aceptada = normalizar(r.get("estado", "")).startswith("aceptad")
        fu = pd.to_numeric(r.get("fraccion_util"), errors="coerce")
        nube_aoi = None if pd.isna(fu) else round(100.0 * (1.0 - float(fu)), 1)
        escena = {"id": r.get("id", ""), "fecha": r.get("fecha"), "nube_aoi_pct": nube_aoi,
                  "estado_original": r.get("estado", "")}
        meta = analizar_id_escena(escena["id"]) or {}
        motivos = motivos_incumplimiento(escena, sede, criterios)
        filas.append({
            "fecha": pd.to_datetime(r.get("fecha"), errors="coerce"),
            "id_escena": escena["id"],
            "sensor": meta.get("sensor_nombre", ""),
            "path_row": meta.get("path_row", ""),
            "tier": meta.get("tier", ""),
            "nubosidad_catalogo_pct": pd.to_numeric(r.get("nubosidad_catalogo"), errors="coerce"),
            "nube_aoi_pct": nube_aoi,
            "estado_original": r.get("estado", ""),
            "fotograma_gif": n_aceptada if aceptada else pd.NA,
            "cumple": not motivos,
            "motivos": "; ".join(motivos),
        })
        n_aceptada += int(aceptada)
    tabla = pd.DataFrame(filas)
    if not tabla.empty:
        tabla["fotograma_gif"] = tabla["fotograma_gif"].astype("Int64")
    return tabla


def filtrar_por_umbral(metadatos: pd.DataFrame, nube_aoi_max_pct: float) -> pd.DataFrame:
    """Escenas que cumplen todos los criterios y además un umbral de AOI igual o más estricto."""
    if metadatos is None or metadatos.empty:
        return pd.DataFrame(columns=getattr(metadatos, "columns", []))
    cumple = metadatos["cumple"].astype(str).str.casefold().isin(["true", "1", "sí", "si"])
    nube = pd.to_numeric(metadatos["nube_aoi_pct"], errors="coerce")
    return metadatos[cumple & nube.le(float(nube_aoi_max_pct))].copy()


def nombre_imagen_escena(id_escena: str) -> str:
    return f"{id_escena}.png"
