"""Pruebas del NetCDF GWSa extendido (GRACE/GRACE-FO − GLDAS, 2002-04 a 2026-06)."""

from pathlib import Path

import numpy as np
import pandas as pd
import pytest

xr = pytest.importorskip("xarray")

RAIZ = Path(__file__).resolve().parents[1]
EXTENDIDO = RAIZ / "data" / "processed" / "gwsa" / "COL_GWS_estimations_2002-2026.nc"
ORIGINAL = RAIZ / "COL_GWS_estimations.nc"
SEDES = RAIZ / "data" / "processed" / "gwsa" / "GWSa_sedes_2002-2026.csv"
CONTINENTALES = ["Bogotá", "Leticia", "Tumaco", "Medellín", "Arauca", "La Paz"]


@pytest.fixture(scope="module")
def ds():
    with xr.open_dataset(EXTENDIDO) as d:
        yield d.load()


def test_cobertura_temporal_llega_a_2026_06(ds):
    meses = list(ds["mes_nominal"].values.astype(str))
    assert meses[0] == "2002-04" and meses[-1] == "2026-06"
    assert ds.attrs["time_coverage_start"] == "2002-04" and ds.attrs["time_coverage_end"] == "2026-06"
    assert pd.Timestamp(ds["time"].values[-1]).strftime("%Y-%m") == "2026-06"
    assert len(meses) == len(set(meses)) == ds.sizes["time"] == 258
    # Brecha GRACE → GRACE-FO sin interpolar: esos meses no tienen paso temporal.
    for m in ["2017-07", "2017-12", "2018-05", "2018-08", "2018-09"]:
        assert m not in meses
    assert "2017-07..2018-05" in ds.attrs["period"]
    # El último mes tiene datos en toda la máscara.
    assert int(ds["GWS_anom"].isel(time=-1).notnull().sum()) > 6000


def test_unidades_y_metadatos_cf(ds):
    v = ds["GWS_anom"]
    assert v.dims == ("time", "lat", "lon")
    assert v.attrs["units"] == "cm"
    assert v.attrs["anomaly_baseline"].startswith("2004-01-01/2009-12-31")
    assert ds.attrs["Conventions"].startswith("CF-")
    assert "RL06.3Mv04" in ds.attrs["source"] and "GLDAS_NOAH025_M v2.1" in ds.attrs["source"]
    assert ds["lat"].attrs["units"] == "degrees_north" and ds["lon"].attrs["units"] == "degrees_east"
    assert ds["time"].attrs.get("bounds") == "time_bnds" and "time_bnds" in ds
    vals = v.values[np.isfinite(v.values)]
    assert -150 < vals.min() and vals.max() < 150  # cm de lámina equivalente, no mm ni m


def test_misma_malla_que_el_original(ds):
    with xr.open_dataset(ORIGINAL) as o:
        assert np.allclose(ds["lat"], o["lat"]) and np.allclose(ds["lon"], o["lon"])
        mascara_o = o["GWS_anom"].notnull().any("time").values
    assert np.array_equal(ds["GWS_anom"].notnull().any("time").values, mascara_o)


def test_series_de_sedes_llegan_a_2026_06():
    s = pd.read_csv(SEDES)
    for sede in CONTINENTALES:
        x = s[(s["sede"] == sede) & s["GWSa_cm"].notna()]
        assert x["mes_nominal"].max() == "2026-06", sede
        assert x["mes_nominal"].min() == "2002-04", sede
    # San Andrés: celda GRACE oceánica y fuera de la malla; la app lo informa sin extrapolar.
    assert "San Andrés" not in set(s["sede"])
