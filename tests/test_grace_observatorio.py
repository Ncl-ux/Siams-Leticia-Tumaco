"""Pruebas unitarias, sin acceder a datos internos ni a Streamlit."""
from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from siams.grace_analisis import (
    combinar_grace_lluvia, correlacion_mensual_desfase,
    preparar_numae_diario, correlacion_lluvia_cambio, calidad_horaria,
)


def test_une_por_mes_nominal_sin_rellenar_faltantes():
    g = pd.DataFrame({'nominal_month': ['2026-01', '2026-03'],
                      'GWSA_B_standard_cm': [1., 3.], 'GWSA_A_original_cm': [2., 4.]})
    p = pd.DataFrame({'fecha': ['2026-01-01', '2026-02-01', '2026-03-01'],
                      'precipitacion_mm_mes': [10., 20., 30.]})
    fechas = pd.date_range('2026-01-01', '2026-02-28', freq='D')
    n = pd.DataFrame({'fecha': fechas, 'precipitacion_mm_dia': 1.})
    combinado = combinar_grace_lluvia(g, p, n)
    assert len(combinado) == 3
    assert pd.isna(combinado.loc[1, 'GWSA_B_cm'])
    assert combinado.loc[1, 'CHIRPS_mm_mes'] == 20.
    assert combinado.loc[1, 'NASA_POWER_mm_mes'] == 28.


def test_no_suma_mes_parcial_de_nasa():
    g = pd.DataFrame({'nominal_month': ['2026-03'],
                      'GWSA_B_standard_cm': [1.], 'GWSA_A_original_cm': [2.]})
    p = pd.DataFrame({'fecha': ['2026-03'], 'precipitacion_mm_mes': [4.]})
    n = pd.DataFrame({'fecha': pd.date_range('2026-03-01', periods=5),
                      'precipitacion_mm_dia': 1.})
    assert pd.isna(combinar_grace_lluvia(g, p, n).NASA_POWER_mm_mes.iloc[0])


def test_lags_mensuales_no_crean_fechas():
    meses = pd.date_range('2025-01-01', periods=20, freq='MS')
    x = np.arange(20, dtype=float) ** 1.2
    d = pd.DataFrame({'Fecha': meses, 'P': x, 'G': np.r_[np.nan, x[:-1]]})
    out = correlacion_mensual_desfase(d, 'P', 'G', max_lag=2, min_pares=5)
    assert out.loc[1, 'r Pearson'] == pytest.approx(1.0)
    assert out.loc[1, 'Meses comunes'] == 19


def test_saltos_de_dias_no_se_confunden_con_cambio_diario():
    d = pd.DataFrame({'fecha': ['2026-01-01', '2026-01-03'],
                      'columna_madrugada_m': [5., 8.],
                      'fraccion_horas_bombeo': [.1, .2],
                      'fraccion_horas_seco': [.1, .3],
                      'lluvia_ideam_mm': [1., 4.],
                      'lluvia_chirps_v3_mm': [1., 4.],
                      'lluvia_imerg_late_mm': [1., 4.],
                      'lluvia_era5_mm': [1., 4.]})
    a = preparar_numae_diario(d)
    assert len(a) == 3
    assert a['cambio_columna_m'].isna().all()
    r = correlacion_lluvia_cambio(a, 'lluvia_ideam_mm', min_pares=2)
    assert r['r Pearson'].isna().all()


def test_banderas_de_profesora_no_se_reclasifican():
    d = pd.DataFrame({'fecha': ['2026-01-01 01:00', '2026-01-01 02:00',
                                '2026-01-01 03:00', '2026-01-01 04:00'],
                      'pozo_id': ['LET-NUMAE', 'LET-NUMAE', 'LET-ARTURO', 'LET-NUMAE'],
                      'calidad': ['ok', 'descenso_brusco_posible_bombeo', 'ok', 'sensor_fuera_del_agua']})
    mensual, horaria = calidad_horaria(d)
    assert mensual.registros.sum() == 3
    assert mensual.marcados.sum() == 2
    assert horaria.loc[horaria.hora.eq(2), 'fraccion_marcados_pct'].iloc[0] == 100.
