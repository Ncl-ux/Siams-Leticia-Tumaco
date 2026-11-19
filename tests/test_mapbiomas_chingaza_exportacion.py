import json, shutil, subprocess
from siams import mapbiomas as m
import math

def test_chingaza_exportaciones():
    rutas=m.encontrar_csv_coberturas('Chingaza','CH')
    assert not rutas['anual'] and len(rutas['serie'])==1
    d=m.cargar_csv_cobertura(str(rutas['serie'][0]))
    years=[str(y) for y in range(1985,2025)]
    assert all(y in d for y in years)
    a=m.preparar_cobertura_nivel(d,'Nivel 1');b=m.preparar_cobertura_nivel(d,'Nivel 2')
    assert len(a)==5 and len(b)==25
    for y in years:assert math.isclose(a[y].sum(),b[y].sum(),abs_tol=1e-5)
    rutas,ambiguos=m.buscar_csv_natural_antropico('Chingaza','CH')
    assert len(rutas)==1 and not ambiguos
    d,meta=m.cargar_csv_natural_antropico(str(rutas[0]))
    assert len(d)==80 and not meta['discrepancias']
    assert all(math.isclose(v,77385.051814,abs_tol=0.01) for v in d.groupby('Año').Valor.sum())

def test_chingaza_mapas():
    for nombre in m.MAPBIOMAS_GIFS_POR_TERRITORIO['Chingaza'].values():
        p=m.buscar_gif_mapbiomas('Chingaza',nombre)
        assert p is not None
        assert p.suffix == '.mp4'
        with p.open('rb') as f:
            assert f.read(8)[4:8] == b'ftyp'
        if shutil.which('ffprobe'):
            info=json.loads(subprocess.check_output(['ffprobe','-v','error','-select_streams','v:0','-show_entries','stream=codec_name,pix_fmt,width,height,duration,nb_frames','-of','json',str(p)]))['streams'][0]
            assert info['codec_name']=='h264' and info['pix_fmt']=='yuv420p'
            assert (info['width'],info['height'])==(600,556)
            assert float(info['duration'])==20 and int(info['nb_frames'])==480
