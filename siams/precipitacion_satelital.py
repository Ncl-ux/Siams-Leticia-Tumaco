"""Panel de contraste de fuentes, independiente de A1, tendencias y GRACE."""
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from .precipitacion_satelital_datos import SEDES, cargar, inventario, pares, ideam_bogota, ideam_leticia
from .catalogo import MESES


def mostrar_precipitacion_satelital(territorio):
    if territorio not in SEDES: return
    sede=SEDES[territorio]
    st.subheader('Precipitación mensual · comparación de fuentes')
    st.caption('CHIRPS (UCSB-CHC), IMERG Final (NASA GPM/GES DISC), NASA POWER (NASA) e IDEAM cuando hay observaciones disponibles. Son estimaciones de celdas y mediciones puntuales independientes; no equivalen a una validación de campo.')
    tabla, avisos = cargar(sede)
    if sede == 'bogota':
        from .ideam_bogota import NOMBRES
        cod = st.selectbox('Estación IDEAM de referencia (Bogotá)', ['21205012','21205230','21200610','21205520'],format_func=lambda c:f'{NOMBRES.get(c,c)} · {c}',key='sat_ideam_bog')
        try:
            obs = ideam_bogota(cod).rename(f'IDEAM {cod}')
            tabla = pd.concat([tabla,obs],axis=1).sort_index()
        except (OSError,ValueError,KeyError) as e:
            avisos['IDEAM']=str(e)
    if sede == 'leticia':
        try:
            tabla = pd.concat([tabla,ideam_leticia().rename('IDEAM 48015050')],axis=1).sort_index()
        except (OSError,ValueError,KeyError) as e:
            avisos['IDEAM']=str(e)
    if avisos:
        with st.expander('Disponibilidad y archivos pendientes',expanded=tabla.empty):
            for nombre,aviso in avisos.items(): st.caption(f'{nombre}: {aviso}')
    tabla = tabla.dropna(axis=1,how="all")
    if tabla.empty:
        st.info('No hay series mensuales disponibles. Ejecuta el actualizador o revisa los archivos locales.')
        return
    tabla=tabla.reindex(pd.date_range(tabla.index.min(),tabla.index.max(),freq='MS'))
    tabla.index.name='fecha'
    st.dataframe(inventario(tabla),hide_index=True,width="stretch")
    sel=st.multiselect('Fuentes a comparar',list(tabla),default=list(tabla),key=f'sat_fuentes_{sede}')
    if not sel: return
    a,b=int(tabla.index.min().year),int(tabla.index.max().year)
    desde,hasta=st.slider('Periodo (años)',a,b,(a,b),key=f'sat_periodo_{sede}') if a<b else (a,b)
    t=tabla.loc[tabla.index.year>=desde,sel]
    t=t.loc[t.index.year<=hasta]
    fig=go.Figure()
    for c in t: fig.add_trace(go.Scatter(x=t.index,y=t[c],name=c,mode='lines',connectgaps=False))
    fig.update_layout(yaxis_title='Precipitación (mm/mes)',legend=dict(orientation='h'))
    st.plotly_chart(fig,width="stretch")
    if len(sel)>1:
        ref=st.selectbox('Referencia para diferencias estadísticas',sel,key=f'sat_ref_{sede}')
        st.dataframe(pares(t,ref).round(3),hide_index=True,width="stretch")
        st.caption('Cada fila usa únicamente fechas comunes con la referencia elegida. El sesgo es fuente menos referencia. Sin imputación.')
        comunes=t.dropna()
        if not comunes.empty:
            r=comunes.groupby(comunes.index.month).mean().reindex(range(1,13))
            n=comunes.groupby(comunes.index.month).size().reindex(range(1,13),fill_value=0)
            fig=go.Figure()
            for c in r: fig.add_trace(go.Scatter(x=MESES,y=r[c],name=c,mode='lines+markers',connectgaps=False,customdata=n,hovertemplate='%{y:.2f} mm · %{customdata} meses<extra>%{fullData.name}</extra>'))
            fig.update_layout(title='Régimen mensual sobre fechas comunes a todas las fuentes',yaxis_title='mm/mes')
            st.plotly_chart(fig,width="stretch")
        else: st.info('No existen meses comunes a todas las fuentes seleccionadas. Selecciona menos fuentes para comparar el régimen.')
    st.download_button('Descargar series mensuales comparadas',t.to_csv().encode('utf-8-sig'),f'precipitacion_fuentes_{sede}.csv','text/csv',key=f'sat_descarga_{sede}')
    st.caption('Sin mes calendario en curso; NASA POWER e IDEAM Bogotá requieren cobertura diaria completa. CHIRPS Final puede faltar en celdas costeras o marinas. IMERG Final tiene latencia de varios meses. No se reemplazan ni combinan versiones.')
