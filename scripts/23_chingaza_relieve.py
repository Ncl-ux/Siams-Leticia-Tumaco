"""GLO-30 DSM: reproyección a UTM 18N a 30 m; pendiente en grados; recorte PNN."""
import argparse, json, math, sys, tempfile
from pathlib import Path
import numpy as np
import rasterio as rio
from rasterio.warp import reproject, Resampling, transform_geom
from rasterio.features import geometry_mask, bounds
from rasterio.transform import from_origin, array_bounds
from rasterio.windows import from_bounds, Window
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import LightSource
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from siams.dem import url_tesela, FUENTE_DEM
BASE=ROOT/'data/processed/chingaza'
CRS='EPSG:32618'; RES=30; NODATA=-9999.

def pendiente(d, res=RES):
    """Diferencias centrales; conserva ausencia de vecinos, sin rellenar."""
    gy,gx=np.gradient(d.astype(float),res,res)
    result=np.degrees(np.arctan(np.hypot(gx,gy)))
    result[~np.isfinite(d)]=np.nan
    return result

def generar(base=BASE, local=None):
    base=Path(base); g=json.loads((base/'pnn_limite_analisis.geojson').read_text(encoding='utf8'))['features'][0]['geometry']
    b=bounds(g); assert math.floor(b[0])==math.floor(b[2]) and math.floor(b[1])==math.floor(b[3]), 'El recorte requiere más de una tesela.'
    url=url_tesela((b[1]+b[3])/2,(b[0]+b[2])/2); geom=transform_geom('EPSG:4326',CRS,g)
    xmin,ymin,xmax,ymax=bounds(geom); xmin=math.floor(xmin/RES)*RES-2*RES; ymin=math.floor(ymin/RES)*RES-2*RES; xmax=math.ceil(xmax/RES)*RES+2*RES; ymax=math.ceil(ymax/RES)*RES+2*RES
    tr=from_origin(xmin,ymax,RES,RES); w,h=round((xmax-xmin)/RES),round((ymax-ymin)/RES)
    d=np.full((h,w),np.nan,dtype='float32')
    with rio.Env(GDAL_DISABLE_READDIR_ON_OPEN='EMPTY_DIR',AWS_NO_SIGN_REQUEST='YES',GDAL_HTTP_TIMEOUT='120'):
        with rio.open(str(local) if local else url) as src:
            if not src.crs: raise ValueError('DEM sin CRS')
            reproject(source=rio.band(src,1),destination=d,src_transform=src.transform,src_crs=src.crs,src_nodata=src.nodata,dst_transform=tr,dst_crs=CRS,dst_nodata=np.nan,resampling=Resampling.bilinear)
    inside=geometry_mask([geom],out_shape=d.shape,transform=tr,invert=True)
    slope=pendiente(d); d[~inside]=np.nan; slope[~inside]=np.nan
    if np.isfinite(d).sum()==0 or np.isfinite(slope).sum()==0: raise ValueError('Sin cobertura válida')
    bins=[0,5,15,25,35,45,90]; counts=np.histogram(slope[np.isfinite(slope)],bins=bins)[0]; valid=int(np.isfinite(slope).sum())
    meta={'fuente':FUENTE_DEM,'url_tesela':url,'archivo_local':bool(local),'crs':CRS,'resolucion_m':RES,'unidad_vertical':'m, EGM2008 (DSM; sin corrección local de sesgo)','area_estudio':'PNN Chingaza, polígono original SIG sin simplificar','cobertura_dem_pct':100*int(np.isfinite(d).sum())/int(inside.sum()),'cobertura_pendiente_pct':100*valid/int(inside.sum()),'min_m':float(np.nanmin(d)),'max_m':float(np.nanmax(d)),'media_m':float(np.nanmean(d)),'pendiente_media_deg':float(np.nanmean(slope)),'clases_pendiente':[{'clase':f'{a}–{b}°','area_ha':float(c)*RES**2/10000,'porcentaje':100*int(c)/valid} for a,b,c in zip(bins,bins[1:],counts)]}
    with tempfile.TemporaryDirectory(dir=base) as tmp:
        t=Path(tmp)
        for name,arr,cmap,unit in [('elevacion',d,'terrain','Elevación (m)'),('pendiente',slope,'YlOrRd','Pendiente (°)')]:
            with rio.open(t/(name+'.tif'),'w',driver='GTiff',height=h,width=w,count=1,dtype='float32',crs=CRS,transform=tr,nodata=NODATA,compress='deflate',predictor=3,tiled=True) as dst: dst.write(np.where(np.isfinite(arr),arr,NODATA).astype('float32'),1)
            fig,ax=plt.subplots(figsize=(8,7),layout='constrained'); im=ax.imshow(arr,extent=(xmin,xmax,ymin,ymax),cmap=cmap,vmin=0 if name=='pendiente' else None,vmax=60 if name=='pendiente' else None); ax.set_title('PNN Chingaza · '+unit); ax.set_xlabel('Este UTM 18N (m)');ax.set_ylabel('Norte UTM 18N (m)'); fig.colorbar(im,ax=ax,shrink=.75,label=unit,extend='max' if name=='pendiente' else 'neither'); fig.savefig(t/(name+'.png'),dpi=150);plt.close(fig)
        (t/'relieve.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2,allow_nan=False),encoding='utf8')
        out=base/'relieve';out.mkdir(exist_ok=True)
        for p in t.iterdir(): p.replace(out/p.name)
    print(json.dumps(meta,ensure_ascii=False,indent=2))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--dem-local',type=Path,help='Tesela original GLO-30 descargada, alternativa a AWS remoto');a=p.parse_args();generar(local=a.dem_local)
