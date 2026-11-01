import importlib.util
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

RAIZ = Path(__file__).resolve().parents[1]


def _script(nombre):
    spec = importlib.util.spec_from_file_location(nombre.replace(".", "_"), RAIZ / "scripts" / nombre)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def test_dem_cotas():
    from siams import dem
    assert dem.SESGO_DEM_M == 1.5
    assert dem.cota_terreno(100.0) == pytest.approx(98.5)
    assert dem.profundidad_desde_presion(17.0, 7.3) == pytest.approx(9.7)
    assert dem.cota_nivel(76.7, 9.7) == pytest.approx(67.0)
    assert "N04_00_W075" in dem.url_tesela(4.6, -74.1)


def test_pozos_y_niveles_coherentes():
    pozos = pd.read_csv(RAIZ / "data/processed/niveles/pozos.csv")
    assert pozos.pozo_id.is_unique
    con = pozos.dropna(subset=["lat"])
    assert set(pozos.pozo_id) - set(con.pozo_id) <= {"BOG-PA27"}  # PA27 sin coordenadas en la nomenclatura OGA
    assert con.lat.between(-5, 13).all() and con.lon.between(-82, -66).all()
    for sede, arch in {"Leticia": "niveles_leticia.csv", "Tumaco": "niveles_tumaco.csv"}.items():
        d = pd.read_csv(RAIZ / "data/processed/niveles" / arch)
        assert set(d.pozo_id) <= set(pozos.pozo_id)
        con = d.dropna(subset=["cota_nivel_msnm", "profundidad_nivel_m"]).merge(pozos[["pozo_id", "cota_terreno_msnm"]])
        assert np.allclose(con.cota_terreno_msnm - con.profundidad_nivel_m, con.cota_nivel_msnm, atol=0.02)
        # Sin profundidad de sensor no se publica cota
        sin = pozos[pozos.prof_sensor_m.isna() & (pozos.sede == sede) & pozos.cota_levantada_msnm.isna()].pozo_id
        assert d[d.pozo_id.isin(sin) & (d.metodo == "transductor")].cota_nivel_msnm.isna().all()


def test_bombeo_tiene_citas():
    d = pd.read_csv(RAIZ / "data/processed/bombeo/resumen_pruebas_bombeo.csv")
    assert d.fuente.notna().all() and d.pagina_pdf.notna().all() and d.cita.notna().all()
    assert set(d.sede) == {"Arauca", "La Paz"}


def test_fq_y_iones():
    d = pd.read_csv(RAIZ / "data/processed/hidrogeoquimica/fq_sedes_iones.csv")
    ok = d[d.nak_estimado_por_diferencia]
    assert np.allclose(ok[["pct_ca", "pct_mg", "pct_nak"]].sum(axis=1), 100, atol=0.1)
    assert np.allclose(ok[["pct_hco3", "pct_cl", "pct_so4"]].sum(axis=1), 100, atol=0.1)


def _fila(**kw):
    base = {"fecha_hora": "2026-10-01 08:30", "sede": "Leticia", "pozo_id": "LET-NUMAE", "tipo_medicion": "nivel_manual",
            "profundidad_nivel_m": "9.7", "referencia": "brocal", "altura_brocal_m": "0.5", "ph": "", "ce_us_cm": "",
            "temperatura_c": "", "od_mg_l": "", "equipo": "", "operador": "PL", "observaciones": ""}
    base.update(kw)
    return base


def test_validador_datos_campo():
    from siams.datos_campo import validar
    pozos = {"LET-NUMAE"}
    assert validar(pd.DataFrame([_fila()]), pozos) == []
    malos = pd.DataFrame([_fila(fecha_hora="01/10/2026"), _fila(pozo_id="X"), _fila(ph="15"),
                          _fila(profundidad_nivel_m="", tipo_medicion="nivel_manual"), _fila(referencia="")])
    err = validar(malos, pozos)
    assert any("Fila 2" in e and "fecha_hora" in e for e in err)
    assert any("Fila 3" in e and "pozo_id" in e for e in err)
    assert any("Fila 4" in e and "ph" in e for e in err)
    assert any("Fila 5" in e and "profundidad" in e for e in err)
    assert any("Fila 6" in e and "referencia" in e for e in err)
    assert validar(pd.DataFrame([{"sede": "Leticia"}]), pozos)[0].startswith("Faltan columnas")


def test_lmwl_recupera_recta():
    from siams.sedes_2026 import lmwl
    x = np.linspace(-12, -2, 20)
    a, b, n = lmwl(pd.DataFrame({"d18O": x, "d2H": 8 * x + 10}))
    assert (round(a, 6), round(b, 6), n) == (8, 10, 20)


def test_actualizacion_semanal_ids_socrata():
    m = _script("12_actualizacion_semanal.py")
    assert m.SOCRATA == {"precipitacion": "s54a-sgyg", "temperatura": "sbwg-7ju4", "nivel_rio": "bdmn-sqnh"}
    assert set(m.ESTACIONES_IDEAM) <= set(m.SEDES)
