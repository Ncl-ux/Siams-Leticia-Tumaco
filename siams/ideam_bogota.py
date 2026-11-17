"""Explorador Bogotá: componentes gráficos del panel de Leticia, datos independientes."""
from html import escape
import numpy as np
import pandas as pd
import streamlit as st
import plotly.graph_objects as go
from .ideam_bogota_datos import BASE, cargar_mensual
from .ideam_leticia import (_css, _metrica, _grafica_mensual, _grafica_anual, _grafica_calendario, _estaciones_html)
from .ideam_leticia_datos import catalogo_estaciones, climatologia_mensual, serie_mensual_anio, tabla_anual, ult_anio_completo

NOMBRES={'21200610':'Jardín Botánico · pluviométrica','21205012':'Universidad Nacional','21205230':'Observatorio Meteorológico Nacional','21205520':'El Dorado Didáctica','21205710':'Jardín Botánico · climatológica'}

def _nombre(c): return f'{NOMBRES.get(str(c),str(c))} · {c}'

def _descarga(label, df, nombre, key):
    st.download_button(label,df.to_csv(index=False).encode('utf-8-sig'),nombre,'text/csv',key=key)

def mostrar_ideam_bogota():
    _css()
    st.markdown('''<div class="siams-ideam-hero"><div class="eyebrow">SIAMS / Clima y datos / Bogotá</div><h1>Precipitación <span>IDEAM</span> · Bogotá</h1><p>Explora los registros DHIME, compara años y reconoce los periodos sin información.</p><div class="ideam-chip">Fuente IDEAM / DHIME · registros definitivos y preliminares</div></div>''',unsafe_allow_html=True)
    try: m=cargar_mensual();q=pd.read_csv(BASE/'inventario.csv',dtype={'CodigoEstacion':str})
    except (OSError,ValueError) as e: st.error(f'Base IDEAM Bogotá no disponible: {e}');return
    p=m[m.Variable.eq('Precipitación')].copy(); q=q[q.Variable.eq('Precipitación')]
    d=p.dropna(subset=['Valor']).rename(columns={'MesFecha':'Fecha'}).copy()
    d['NombreEstacion']=d.CodigoEstacion.map(NOMBRES);d['Anio']=d.Fecha.dt.year;d['Mes']=d.Fecha.dt.month
    codigos=sorted(p.CodigoEstacion.unique(),key=lambda c:-int(p.loc[p.CodigoEstacion.eq(c),'Dias'].sum()))
    a,b=st.columns([1.6,1]);
    with a: codigo=st.selectbox('Estación IDEAM',codigos,format_func=_nombre,key='ideam_bog_estacion')
    e=d[d.CodigoEstacion.eq(codigo)].copy(); raw=p[p.CodigoEstacion.eq(codigo)].copy()
    years=sorted(raw.MesFecha.dt.year.unique(),reverse=True);defecto=ult_anio_completo(e)
    with b: anio=st.selectbox('Año de comparación',years,index=years.index(defecto) if defecto in years else 0,key=f'ideam_bog_anio_{codigo}')
    tabla=tabla_anual(e).set_index('Anio').reindex(range(min(years),max(years)+1)).reset_index()
    tabla['Meses']=tabla.Meses.fillna(0).astype(int);tabla['Completo']=tabla.Meses.eq(12)
    fila=tabla[tabla.Anio.eq(anio)].iloc[0]
    cols=st.columns(4,gap='small')
    with cols[0]: _metrica('◉ Registros',f'{int(p.Dias.sum()):,}'.replace(',','.'),'Días observados · todas las estaciones')
    with cols[1]: _metrica('⌖ Estaciones',str(len(codigos)),'Con precipitación disponible')
    with cols[2]: _metrica('▦ Periodo global',f'{p.MesFecha.min().year}–{p.MesFecha.max().year}','Incluye periodos sin información')
    with cols[3]: _metrica(f'Precipitación {anio}',f'{fila.Precipitacion_mm:,.1f} mm' if pd.notna(fila.Precipitacion_mm) else 'Sin dato',f'{fila.Meses}/12 meses completos',teal=True)
    with st.expander('Periodo histórico de referencia'):
        lo,hi=st.slider('Años del promedio',min(years),max(years),(min(years),max(years)),key=f'ideam_bog_ref_{codigo}')
    clim,valid=climatologia_mensual(e,lo,hi);actual=serie_mensual_anio(e,anio)
    left,right=st.columns([1.55,1],gap='medium')
    with left:
        with st.container(border=True):
            st.markdown('<div class="siams-ideam-head">▥ &nbsp;Precipitación mensual</div>',unsafe_allow_html=True)
            st.caption(f'{_nombre(codigo)} · Comparación con {anio}')
            st.plotly_chart(_grafica_mensual(clim,actual,anio,f'{lo}–{hi}'),use_container_width=True)
            st.caption(f'Promedio de {len(valid)} años completos. Meses incompletos excluidos, sin interpolar. No equivale a normal climática oficial.')
    with right:
        with st.container(border=True):
            st.markdown('<div class="siams-ideam-head">⌖ &nbsp;Estaciones IDEAM</div>',unsafe_allow_html=True)
            st.caption('Cobertura diaria dentro del intervalo observado de cada estación')
            for r in q.sort_values('CoberturaPct',ascending=False).itertuples():
                pct=float(r.CoberturaPct)
                st.markdown(f'<div class="siams-ideam-station"><div class="st-name">{escape(_nombre(r.CodigoEstacion))}</div><div class="st-data">{r.Dias} días · {pct:.1f}% de cobertura</div><div class="st-data">{r.Inicio} a {r.Fin} · {int(r.AniosCompletos)} años completos</div><div class="siams-ideam-track"><div class="siams-ideam-fill" style="width:{pct:.1f}%"></div></div></div>',unsafe_allow_html=True)
            if valid: st.caption(f'Promedio anual de referencia: {clim.Media_mm.sum():,.1f} mm ({len(valid)} años completos).')
            st.caption(f'Calidad de estación: {int(raw.Definitivos.sum())} días definitivos de {int(raw.Dias.sum())}.')
    left,right=st.columns([1.1,1],gap='medium')
    with left:
        with st.container(border=True):
            st.markdown('<div class="siams-ideam-head">▥ &nbsp;Historia de la lluvia</div>',unsafe_allow_html=True)
            st.caption('Suma de meses completos · tonos claros = años parciales; no es un total anual si faltan meses')
            st.plotly_chart(_grafica_anual(tabla,anio),use_container_width=True)
    with right:
        with st.container(border=True):
            st.markdown('<div class="siams-ideam-head">▦ &nbsp;Calendario histórico de precipitaciones</div>',unsafe_allow_html=True)
            st.caption('Cada celda es un mes completo · gris = datos incompletos o ausentes')
            matrix=e.pivot(index='Anio',columns='Mes',values='Valor').reindex(index=range(min(years),max(years)+1),columns=range(1,13))
            if matrix.notna().any().any():
                f=_grafica_calendario(matrix);f.update_traces(zmax=max(1,float(np.nanmax(matrix.to_numpy(dtype=float)))))
                st.plotly_chart(f,use_container_width=True)
    with st.expander('Metodología, control de calidad y descargas'):
        st.write('Fuente: ZIP DHIME del semillero, día pluviométrico convencional (mm). Los meses parciales se conservan en la tabla de auditoría, no se anualizan ni se imputan. Las estaciones no se mezclan.')
        st.dataframe(raw,hide_index=True,use_container_width=True)
        _descarga('Descargar serie mensual y cobertura',raw,f'SIAMS_IDEAM_Bogota_{codigo}_mensual.csv','bog_mensual')
        _descarga('Descargar resumen anual',tabla,f'SIAMS_IDEAM_Bogota_{codigo}_anual.csv','bog_anual')
        st.download_button('Descargar registros diarios consolidados de Bogotá',(BASE/'diario.csv').read_bytes(),'SIAMS_IDEAM_Bogota_diario.csv','text/csv',key='bog_diario')

def mostrar_homogeneidad_bogota():
    st.title('🌧️ Homogeneidad (A1) · Bogotá')
    st.caption('IDEAM / DHIME · análisis exploratorio, independiente de NASA POWER')
    try:
        m=cargar_mensual();r=pd.read_csv(BASE/'homogeneidad.csv',dtype={'estacion':str,'referencia':str});q=pd.read_csv(BASE/'inventario.csv',dtype={'CodigoEstacion':str})
    except (OSError,ValueError) as e:st.error(f'No se encontró el diagnóstico A1: {e}');return
    st.markdown('**Método:** anomalías mensuales estandarizadas por mes calendario; SNHT A1 original con 999 permutaciones de bloques-año (mínimo 48 meses y 24 observaciones por segmento, además del 10 % por segmento). Pettitt sobre las mismas anomalías, valor p aproximado. Nivel de alerta 5 %.')
    st.warning('Tamizaje, no certificación de homogeneidad. Los archivos XLSX con varias temperaturas se identificaron por orden de cabecera y bloques cronológicos; esos resultados son exploratorios. La prueba relativa no atribuye el cambio a una estación por sí sola.')
    a,b=st.columns(2)
    with a:var=st.selectbox('Variable',sorted(m.Variable.unique()),index=sorted(m.Variable.unique()).index('Precipitación'),key='bog_a1_var')
    with b:crit=st.radio('Cobertura mensual',['100%','≥90% (sensibilidad)'],key='bog_a1_cob',horizontal=True)
    col='Valor' if crit=='100%' else 'Valor90'
    st.caption('El criterio de sensibilidad reproduce el umbral A1 de Tumaco. Los totales de lluvia de meses con días faltantes son parciales, no estimaciones del total mensual.')
    qq=q[q.Variable.eq(var)].copy();qq['Estación']=qq.CodigoEstacion.map(_nombre)
    st.subheader('Disponibilidad y calidad');st.dataframe(qq[['Estación','Inicio','Fin','Dias','CoberturaPct','AniosCompletos','Definitivos','Inferidos']].round(2),hide_index=True,use_container_width=True)
    sub=r[r.variable.eq(var)&r.criterio.eq(crit)].copy()
    sub['Estación']=sub.estacion.map(_nombre);sub['Referencia']=sub.referencia.map(lambda c:'Absoluto' if c=='—' else _nombre(c))
    sub['Lectura']=np.where(sub.estado.ne('calculado'),'Insuficiente',np.where((sub.p_bloques<.05)&(sub.pettitt_p<.05),'Alerta en ambas pruebas',np.where((sub.p_bloques<.05)|(sub.pettitt_p<.05),'Alerta en una prueba','Sin evidencia de cambio')))
    st.subheader('Pettitt y SNHT absoluto / relativo')
    fields=['Estación','Referencia','estado','n','desde','hasta','T_SNHT','p_bloques','corte','pettitt_K','pettitt_p','pettitt_corte','Lectura']
    st.dataframe(sub[fields].round(5),hide_index=True,use_container_width=True)
    st.caption('Los cortes indican la última observación antes del cambio candidato, no necesariamente el mes calendario inmediatamente anterior. Para tendencia climática de largo plazo, el objetivo sigue siendo al menos 25 años con cobertura suficiente.')
    st.subheader('Contraste entre estaciones')
    codes=sorted(m[m.Variable.eq(var)].CodigoEstacion.unique());a,b=st.columns(2)
    with a:code=st.selectbox('Estación objetivo',codes,format_func=_nombre,key=f'bog_a1_obj_{var}')
    others=[c for c in codes if c!=code]
    with b:ref=st.selectbox('Referencia',others,format_func=_nombre,key=f'bog_a1_ref_{var}_{code}') if others else None
    mm=m[m.Variable.eq(var)]; x=mm[mm.CodigoEstacion.eq(code)].set_index('MesFecha')[col]
    fig=go.Figure(); idx=pd.date_range(x.index.min(),x.index.max(),freq='MS');fig.add_scatter(x=idx,y=x.reindex(idx),name=_nombre(code),connectgaps=False)
    if ref:
        y=mm[mm.CodigoEstacion.eq(ref)].set_index('MesFecha')[col];idx2=pd.date_range(y.index.min(),y.index.max(),freq='MS');fig.add_scatter(x=idx2,y=y.reindex(idx2),name=_nombre(ref),connectgaps=False)
    fig.update_layout(yaxis_title='mm/mes' if var=='Precipitación' else '%' if var=='Humedad relativa' else '°C',height=320);st.plotly_chart(fig,use_container_width=True)
    if ref:
        xy=pd.concat([x.rename('x'),y.rename('y')],axis=1,join='inner').dropna().sort_index()
        if len(xy)>=3:
            an=xy-xy.groupby(xy.index.month).transform('mean');st.caption(f'{len(xy)} meses coincidentes · Pearson: {xy.x.corr(xy.y):.3f} · Pearson de anomalías: {an.x.corr(an.y):.3f}')
            if var=='Precipitación':
                f=go.Figure(go.Scatter(x=xy.y.cumsum(),y=xy.x.cumsum(),mode='lines+markers',text=xy.index.strftime('%Y-%m'),hovertemplate='%{text}<br>Referencia %{x:.1f} mm<br>Objetivo %{y:.1f} mm<extra></extra>'));f.update_layout(title='Curva de doble masa · meses comunes',xaxis_title=_nombre(ref)+' (mm acumulados)',yaxis_title=_nombre(code)+' (mm acumulados)',height=390);st.plotly_chart(f,use_container_width=True)
            else:st.caption('Para temperatura el contraste relativo usa diferencias mensuales, no cocientes acumulados.')
        else:st.info('Cruce temporal insuficiente para una comparación útil.')
    _descarga('Descargar resultados de homogeneidad',r,'SIAMS_A1_Bogota.csv','bog_a1_down')
    _descarga('Descargar inventario completo',q,'SIAMS_IDEAM_Bogota_inventario.csv','bog_a1_inv')
