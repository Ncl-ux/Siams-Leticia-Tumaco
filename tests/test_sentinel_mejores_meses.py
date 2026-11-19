import json
from pathlib import Path
import tempfile
import unittest
from siams.sentinel_mejores_meses import clave_territorio, cargar_coleccion

class TestSentinelMejoresMeses(unittest.TestCase):
    def test_normalizacion(self):
        self.assertEqual(clave_territorio('San Andrés'), 'san_andres')
        self.assertEqual(clave_territorio('Bogotá'), 'bogota')
        self.assertEqual(clave_territorio('La Paz'), 'la_paz')
    def test_sin_catalogo(self):
        with tempfile.TemporaryDirectory() as t:
            self.assertIsNone(cargar_coleccion(t,'Bogotá'))
    def test_catalogo_y_archivos(self):
        with tempfile.TemporaryDirectory() as t:
            base = Path(t)
            video = base/'ndvi.mp4'; video.write_bytes(b'test')
            entrada = {'publicar':False,'productos':{'NDVI':'ndvi.mp4','SCL':'../fuera.mp4','MNDWI':'no_existe.mp4'}}
            (base/'mejores_meses_manifest.json').write_text(json.dumps({'territorios':{'bogota':entrada}}),encoding='utf-8')
            meta, archivos = cargar_coleccion(base,'Bogotá')
            self.assertFalse(meta['publicar'])
            self.assertEqual(archivos, {'NDVI':video.resolve()})
            self.assertIsNone(cargar_coleccion(base,'Leticia'))
