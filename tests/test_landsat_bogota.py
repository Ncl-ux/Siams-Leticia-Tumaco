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


def test_chingaza_pnn_y_temporada():
    import pytest
    pytest.importorskip('rasterio')
    c = cargar_criterios()
    assert c['ventana_estacional']['chingaza'] == [12,1,2]
    assert mod.rangos_temporada(c['ventana_estacional']['chingaza'], 2025) == ('2024-12-01', '2025-02-28')
    crs,tr,n,mask,bbox,radio = mod.malla_pnn_chingaza(RAIZ / 'data/processed/chingaza/pnn_limite_analisis.geojson')
    assert crs == 'EPSG:32618' and tr.a == 30 and tr.e == -30
    assert mask.shape == (n,n) and 770 < mask.sum()*900/1e6 < 780
    assert 0 < mask.sum() < n*n

def test_secuencia_chingaza_no_mezcla_sedes(tmp_path):
    for t,sede,pub in [(2023,'Chingaza',True),(2024,'Bogotá',True),(2025,'Chingaza',False),(2026,'Chingaza',True)]:
        (tmp_path / f'{t}.jpg').write_bytes(b'jpg')
        d = dict(sede=sede, temporadas=[t], publicable=pub, aoi_sin_observacion_pct=2,
                 ventana_meses=[12,1,2], imagenes={'color_natural':f'{t}.jpg'})
        (tmp_path/f'{t}_compuesto.json').write_text(json.dumps(d), encoding='utf-8')
    assert [r['temporada'] for r in fotogramas_aprobados(tmp_path,5,'Chingaza',[12,1,2])] == [2023,2026]


def test_solo_escenas_no_activa_compuestos(monkeypatch):
    llamadas = []
    monkeypatch.setattr(mod, 'cargar_criterios', lambda: {})
    monkeypatch.setattr(mod, 'compuesto_sede', lambda sede, ts, *args, **kwargs: llamadas.append((sede, ts, kwargs)))
    mod.main(['--sede','Chingaza','--temporadas','2025','2023','2025','--solo-escenas'])
    assert llamadas == [('Chingaza', [2023,2025], {'solo_escenas':True})]
