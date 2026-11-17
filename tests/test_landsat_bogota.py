import importlib.util
import json
from pathlib import Path

from siams.landsat_calidad import cargar_criterios
from siams.landsat_secuencia import fotogramas_aprobados

RAIZ = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('compuestos', RAIZ / 'scripts/08_landsat_compuestos_stac.py')
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


def test_bogota_config():
    c = cargar_criterios()
    assert c['buffer_km']['bogota'] == 20
    assert mod.SEDES['Bogotá'] == ((4.6386, -74.0841), 'Bogota')
    assert mod.rangos_temporada(c['ventana_estacional']['bogota'], 2025) == ('2024-12-01', '2025-02-28')


def test_compuestos_por_temporada(monkeypatch):
    llamadas = []
    monkeypatch.setattr(mod, 'compuesto_sede', lambda sede, ts, *args: llamadas.append((sede, ts)))
    mod.main(['--sede', 'Bogotá', '--temporadas', '2025', '2023', '2025', '--por-temporada'])
    assert llamadas == [('Bogotá', [2023]), ('Bogotá', [2025])]


def test_secuencia_solo_aprobados(tmp_path):
    for t, pub, falta in [(2023, True, 2), (2024, False, 2), (2025, True, 4), (2026, True, 6)]:
        (tmp_path / f'{t}.jpg').write_bytes(b'jpg')
        d = dict(sede='Bogotá', temporadas=[t], publicable=pub, aoi_sin_observacion_pct=falta,
                 ventana_meses=[12, 1, 2], imagenes={'color_natural': f'{t}.jpg'})
        (tmp_path / f'{t}_compuesto.json').write_text(json.dumps(d), encoding='utf-8')
    assert [r['temporada'] for r in fotogramas_aprobados(tmp_path, 5)] == [2023, 2025]


def test_secuencia_no_lectura_externa(tmp_path):
    d = dict(sede='Bogotá', temporadas=[2024], publicable=True, aoi_sin_observacion_pct=1,
             ventana_meses=[12, 1, 2], imagenes={'color_natural': '../x.jpg'})
    (tmp_path / 'x_compuesto.json').write_text(json.dumps(d), encoding='utf-8')
    assert fotogramas_aprobados(tmp_path, 5) == []
