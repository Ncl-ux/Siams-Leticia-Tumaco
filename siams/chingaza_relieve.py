"""Relieve Chingaza y preparación de coberturas, sin dependencias ráster en Streamlit."""
import json
import pandas as pd
import streamlit as st
from .chingaza_datos import BASE

def mostrar_relieve():
    p=BASE/'relieve'; meta=p/'relieve.json'
    st.subheader('Relieve y pendientes · PNN Chingaza')
    if not meta.is_file():
        st.info('Pendiente generar los productos Copernicus GLO-30.'); return
    m=json.loads(meta.read_text(encoding='utf8'))
    st.caption(m['fuente']+' · '+m['area_estudio']+' · '+m['unidad_vertical'])
    a,b,c=st.columns(3);a.metric('Elevación mínima',f"{m['min_m']:,.0f} m");b.metric('Elevación máxima',f"{m['max_m']:,.0f} m");c.metric('Pendiente media',f"{m['pendiente_media_deg']:.1f}°")
    e,s=st.tabs(['Elevación','Pendiente'])
    for tab,n in [(e,'elevacion'),(s,'pendiente')]:
        with tab:
            st.image(str(p/(n+'.png')),width='stretch')
            st.download_button('Descargar GeoTIFF',data=(p/(n+'.tif')).read_bytes(),file_name=f'chingaza_{n}_30m.tif',mime='image/tiff',key='chingaza_relieve_'+n)
    df=pd.DataFrame(m['clases_pendiente']);st.bar_chart(df.set_index('clase').porcentaje,y_label='% del área válida');st.dataframe(df,hide_index=True,width='stretch')
    st.caption(f"Cobertura válida: DEM {m['cobertura_dem_pct']:.2f} %, pendiente {m['cobertura_pendiente_pct']:.2f} %. Clases descriptivas en grados; área estimada por píxeles UTM, no área legal del parque.")
    st.caption('GLO-30 es un modelo digital de superficie (DSM), no de terreno desnudo. No se transfiere a Chingaza el sesgo empírico de Leticia. Pendiente calculada por diferencias centrales en grilla métrica.')

def mostrar():
    st.title('🌿 Cobertura y relieve · Chingaza')
    a,b=st.tabs(['Coberturas MapBiomas','Mapas y relieve'])
    with a:
        from .mapbiomas import mostrar_coberturas_mapbiomas
        mostrar_coberturas_mapbiomas("Chingaza")
    with b: mostrar_relieve()
