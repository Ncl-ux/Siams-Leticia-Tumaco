"""Criterios de calidad Landsat (siams/landsat.py, config/landsat_criterios.toml)."""
from pathlib import Path

import pandas as pd
import pytest

from siams.landsat import (
    analizar_id_escena,
    cargar_criterios,
    evaluar_control_escenas,
    filtrar_por_umbral,
    motivos_incumplimiento,
    nombre_imagen_escena,
)

RAIZ = Path(__file__).resolve().parents[1]
SEDES = {"Arauca": "Arauca", "La Paz": "La Paz", "Leticia": "Leticia", "Medellin": "Medellín",
         "San Andres": "San Andrés", "Tumaco": "Tumaco"}


@pytest.fixture(scope="module")
def criterios():
    return cargar_criterios()


def test_configuracion_carga(criterios):
    g = criterios["general"]
    assert 10 <= g["nube_aoi_max_pct"] <= 20
    assert g["coleccion"] == "02" and g["tiers_permitidos"] == ["T1"]
    for sede in ["arauca", "la paz", "leticia", "medellin", "san andres", "tumaco", "bogota"]:
        assert criterios["ventana_estacional"][sede], sede
        if sede != "bogota":  # Bogotá no tiene carpeta Landsat
            assert criterios["buffer_km"][sede] > 0
    assert criterios["ventana_estacional"]["leticia"] == [6, 7, 8, 9]
    assert criterios["ventana_estacional"]["tumaco"] == [7, 8, 9, 10]


def test_analizar_ids_gee_y_usgs():
    a = analizar_id_escena("LC09_L2SP_006055_20241208_02_T1")
    assert a["sensor"] == "LC09" and a["path_row"] == "006/055" and a["tier"] == "T1"
    assert a["fecha_adquisicion"] == pd.Timestamp("2024-12-08")
    b = analizar_id_escena("LE07_L2SP_004063_20100810_20200911_02_T2")
    assert b["sensor"] == "LE07" and b["tier"] == "T2" and b["coleccion"] == "02"
    assert analizar_id_escena("S2A_MSIL2A_20240101") is None


def _motivos(criterios, id_, sede="Arauca", nube=5.0, estado="aceptada"):
    return motivos_incumplimiento({"id": id_, "nube_aoi_pct": nube, "estado_original": estado}, sede, criterios)


def test_escena_que_cumple(criterios):
    assert _motivos(criterios, "LC09_L2SP_006055_20241208_02_T1") == []
    assert _motivos(criterios, "LC08_L2SP_004063_20230810_02_T1", sede="Leticia") == []


@pytest.mark.parametrize("id_, sede, nube, estado, texto", [
    ("LC08_L2SP_006055_20240110_02_T2", "Arauca", 5.0, "aceptada", "Tier 1"),
    ("LE07_L2SP_006055_20100110_02_T1", "Arauca", 5.0, "aceptada", "SLC apagado"),
    ("LC08_L2SP_006055_20240610_02_T1", "Arauca", 5.0, "aceptada", "ventana estacional"),
    ("LC08_L2SP_004063_20240110_02_T1", "Leticia", 5.0, "aceptada", "ventana estacional"),
    ("LC08_L2SP_006055_20240110_02_T1", "Arauca", 35.0, "aceptada", "AOI sin dato útil"),
    ("LC08_L2SP_006055_20240110_02_T1", "Arauca", None, "aceptada", "sin nubosidad calculada"),
    ("LC08_L2SP_006055_20240110_02_T1", "Arauca", 5.0, "descartada", "descartada"),
    ("LC08_L1TP_006055_20240110_02_T1", "Arauca", 5.0, "aceptada", "L2SP"),
    ("XXXX", "Arauca", 5.0, "aceptada", "no reconocido"),
])
def test_motivos_de_rechazo(criterios, id_, sede, nube, estado, texto):
    motivos = _motivos(criterios, id_, sede=sede, nube=nube, estado=estado)
    assert any(texto in m for m in motivos), motivos


def test_le07_antes_del_fallo_slc_se_admite(criterios):
    assert _motivos(criterios, "LE07_L2SP_006055_20030110_02_T1") == []


def test_evaluar_control_y_fotogramas(criterios):
    control = pd.DataFrame({
        "fecha": ["2024-01-10", "2024-06-10", "2024-02-01"],
        "id": ["LC08_L2SP_006055_20240110_02_T1", "LC08_L2SP_006055_20240610_02_T1",
               "LC08_L2SP_006055_20240201_02_T1"],
        "nubosidad_catalogo": [3, 4, 80],
        "estado": ["aceptada", "aceptada", "descartada"],
        "fraccion_util": [0.95, 0.99, 0.10],
    })
    t = evaluar_control_escenas(control, "Arauca", criterios)
    assert list(t["cumple"]) == [True, False, False]
    assert list(t["fotograma_gif"].astype("object")) == [0, 1, pd.NA]
    assert t.loc[0, "nube_aoi_pct"] == pytest.approx(5.0)


def test_filtrar_por_umbral_solo_mas_estricto():
    m = pd.DataFrame({"id_escena": list("abcd"), "cumple": [True, True, False, True],
                      "nube_aoi_pct": [2.0, 15.0, 1.0, None]})
    assert list(filtrar_por_umbral(m, 20)["id_escena"]) == ["a", "b"]
    assert list(filtrar_por_umbral(m, 10)["id_escena"]) == ["a"]
    assert filtrar_por_umbral(m.iloc[0:0], 10).empty


@pytest.mark.parametrize("carpeta, sede", SEDES.items())
def test_repositorio_solo_contiene_escenas_que_cumplen(criterios, carpeta, sede):
    d = RAIZ / "Landsat" / carpeta
    meta = pd.read_csv(d / "metadatos_escenas.csv")
    # Los metadatos guardados coinciden con lo que dan los criterios vigentes.
    recalculado = evaluar_control_escenas(pd.read_csv(d / "Control_escenas.csv"), sede, criterios)
    assert list(meta["cumple"]) == list(recalculado["cumple"])
    cumplen = set(meta.loc[meta["cumple"], "id_escena"])
    imagenes = {p.name for p in (d / "escenas").glob("*")} if (d / "escenas").is_dir() else set()
    assert imagenes == {nombre_imagen_escena(i) for i in cumplen}
    assert not list(d.glob("*.gif")), "no deben quedar GIF con escenas que no cumplen"
    for j in (d / "compuestos").glob("*_compuesto.json") if (d / "compuestos").is_dir() else []:
        import json
        info = json.loads(j.read_text(encoding="utf-8"))
        assert info["sensores"] and set(info["sensores"]) <= {"landsat-8", "landsat-9"}
        for nombre in info["imagenes"].values():
            assert (d / "compuestos" / nombre).is_file()
