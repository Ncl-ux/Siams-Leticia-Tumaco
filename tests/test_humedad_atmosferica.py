from pathlib import Path
from siams.humedad_atmosferica import buscar_humedad_territorio, CARPETA_HUMEDAD


def test_insumos_humedad():
    for nombre in ['Arauca','La Paz','Medellín','Tumaco']:
        archivos = buscar_humedad_territorio(nombre)
        assert set(archivos) == {'video','climatologia'}
        assert archivos['video'].suffix == '.mp4'
        assert archivos['climatologia'].suffix == '.png'
    for nombre in ['Bogotá','Leticia','San Andrés','Chingaza']:
        assert buscar_humedad_territorio(nombre) == {}


def test_resolucion_normalizada(tmp_path):
    carpeta = tmp_path / 'Medellin'
    carpeta.mkdir()
    video = carpeta / 'origen_humedad_1990-2019.mp4'
    video.write_bytes(b'video')
    assert buscar_humedad_territorio(' MEDELLÍN ',tmp_path) == {'video':video}
    assert buscar_humedad_territorio('La Paz',tmp_path) == {}
    video.write_bytes(b'')
    assert buscar_humedad_territorio('Medellin',tmp_path) == {}
