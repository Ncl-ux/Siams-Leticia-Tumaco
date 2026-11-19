"""Deriva GeoJSON de SIG, sin atributos originales ni puntos sensibles. Requiere fiona, shapely, pyproj."""
import argparse,json,sys
from pathlib import Path
import fiona
from shapely.geometry import shape,mapping
from shapely.ops import transform
try: from shapely import make_valid
except ImportError: from shapely.validation import make_valid
from pyproj import Transformer,Geod
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from siams.chingaza_datos import BASE
CAPAS={'Chingaza':'PNN Chingaza','Chingaza_Buffer':'Zona de influencia','Full_Chuza_Catchment':'Cuenca río Chuza','Sampling_Catchment_Chuza':'Cuenca de muestreo Chuza','Cuenca_Playa_Frai_Frio':'Cuenca Playa–Fray–Frío','Piedras_Gordas':'Cuenca Piedras Gordas','DrainageLine_Chuza':'Drenaje Chuza','DrainageLine_Playa_Frai_Frio':'Drenaje Playa–Fray–Frío','DrainageLine_PiedrasGordas':'Drenaje Piedras Gordas'}

def generar(origen,base=BASE):
    origen=Path(origen); base=Path(base); base.mkdir(parents=True,exist_ok=True); meta=[]; ref=None
    for nombre,titulo in CAPAS.items():
        features=[]; repaired=0
        with fiona.open(origen/(nombre+'.shp')) as src:
            if not src.crs: raise ValueError(f'CRS ausente: {nombre}')
            t=Transformer.from_crs(src.crs,4326,always_xy=True)
            for f in src:
                g=transform(t.transform,shape(f.geometry))
                if not g.is_valid:
                    repaired+=1; g=make_valid(g)
                if g.is_empty or not g.is_valid: raise ValueError(f'Geometría no válida: {nombre}')
                if nombre=='Chingaza':
                    pt=g.representative_point(); ref={'lat':round(pt.y,6),'lon':round(pt.x,6),'criterio':'Punto interior representativo del polígono PNN Chingaza entregado; no corresponde al centro del embalse ni al promedio de una cuenca.'}
                g=g.simplify(0.0001,preserve_topology=True)
                features.append({'type':'Feature','properties':{'capa':titulo},'geometry':mapping(g)})
        (base/(nombre+'.geojson')).write_text(json.dumps({'type':'FeatureCollection','features':features},ensure_ascii=False,separators=(',',':')),encoding='utf-8')
        meta.append({'archivo':nombre+'.geojson','nombre':titulo,'elementos':len(features),'geometrias_reparadas':repaired,'fuente':'Proyecto Chingaza / SIG / Geodatabase / '+nombre+'.shp','crs_salida':'EPSG:4326'})
    if not ref: raise ValueError('Sin referencia PNN')
    (base/'cartografia.json').write_text(json.dumps({'referencia':ref,'capas':meta,'simplificacion_grados':0.0001,'nota':'Cartografía derivada para visualización. Fuente primaria y fecha de cada capa pendientes de confirmar; no usar para medición de área o modelación.'},ensure_ascii=False,indent=2),encoding='utf-8')
    print(ref, sum(c['elementos'] for c in meta),'elementos')
if __name__=='__main__':
    p=argparse.ArgumentParser(); p.add_argument('directorio_shp'); a=p.parse_args(); generar(a.directorio_shp)
