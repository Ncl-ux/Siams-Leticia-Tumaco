"""Paneles Chingaza: cartografía, observaciones mensuales y clima satelital."""

import json

import pandas as pd

import plotly.graph_objects as go

import streamlit as st

from .chingaza_datos import BASE, NASA_COLUMNAS, referencia, leer_eaab, leer_nasa, climatologia_nasa, anual_completo



FUENTE='EAAB E.S.P. · Sistema de Información Hidrológica (SIH), reporte 2 de febrero de 2024; archivo INFORMACIÓN CHINGAZA_Acueducto.xlsx, proyecto Chingaza.'



# SIAMS_CHINGAZA_IDEAM

from .chingaza_ideam import mostrar_ideam, mostrar_inventario, agregar_mapa



def segmentos(g):

    t=g['type']; c=g.get('coordinates',[])

    if t=='LineString': yield c

    elif t in ('MultiLineString','Polygon'): yield from c

    elif t=='MultiPolygon':

        for p in c: yield from p

    elif t=='GeometryCollection':

        for h in g['geometries']: yield from segmentos(h)



def mapa():

    st.title('🗺️ Chingaza · Cuencas y red de drenaje')

    meta=json.loads((BASE/'cartografia.json').read_text(encoding='utf-8')); ref=meta['referencia']; capas=meta['capas']

    elegidas=st.multiselect('Capas visibles',[c['nombre'] for c in capas],default=['PNN Chingaza','Cuenca río Chuza','Drenaje Chuza','Cuenca Playa–Fray–Frío','Cuenca Piedras Gordas'],key='chingaza_capas')

    fig=go.Figure(); colores=['#198b68','#999999','#d98732','#b44bb3','#a6532a','#6478bb','#2076bc','#2ca2c9','#3b8e93']

    for i,capa in enumerate(capas):

        if capa['nombre'] not in elegidas: continue

        data=json.loads((BASE/capa['archivo']).read_text(encoding='utf-8')); lat=[]; lon=[]

        for f in data['features']:

            for seg in segmentos(f['geometry']):

                for p in seg: lon.append(p[0]); lat.append(p[1])

                lat.append(None);lon.append(None)

        fig.add_trace(go.Scattermap(lat=lat,lon=lon,mode='lines',line=dict(width=2,color=colores[i]),name=capa['nombre'],hoverinfo='name'))

    fig.add_trace(go.Scattermap(lat=[ref['lat']],lon=[ref['lon']],mode='markers',marker=dict(size=11,color='#cd6532'),name='Referencia satelital puntual'))

    if st.checkbox('Mostrar estaciones IDEAM',value=True,key='chingaza_mapa_ideam'):

        agregar_mapa(fig)

    fig.update_layout(map=dict(style='open-street-map',center=dict(lat=ref['lat'],lon=ref['lon']),zoom=9),height=620,margin=dict(l=0,r=0,t=0,b=0),legend=dict(orientation='h'))

    st.plotly_chart(fig,width='stretch')

    st.caption('Fuente: Proyecto Chingaza · SIG / Geodatabase. '+meta['nota'])

    st.dataframe(pd.DataFrame(capas),hide_index=True,width='stretch')

    st.caption('Punto de referencia para los productos satelitales: '+ref['criterio'])



def observaciones(variable=None, tendencias=False):

    d=leer_eaab(); inv=pd.read_csv(BASE/'eaab_estaciones.csv',dtype={'estacion':str}); st.caption(FUENTE)

    if variable is None: variable=st.radio('Variable observada',['Precipitación','Caudal'],horizontal=True,key='chingaza_var')

    info=inv[inv.variable.eq(variable)]; cod=st.selectbox('Estación EAAB',info.estacion.tolist(),format_func=lambda c: f'{info.set_index("estacion").loc[c,"nombre"]} · {c}',key=f'chingaza_est_{variable}')

    serie=d[d.estacion.eq(cod)&d.variable.eq(variable)].sort_values('fecha'); unidad=serie.unidad.iloc[0]

    a,b=int(serie.fecha.dt.year.min()),int(serie.fecha.dt.year.max()); ini,fin=st.slider('Periodo (años)',a,b,(a,b),key=f'chingaza_periodo_{variable}') if a<b else (a,b)

    s=serie[serie.fecha.dt.year.between(ini,fin)].copy(); n=s.valor.count(); c1,c2,c3=st.columns(3); c1.metric('Meses válidos',int(n)); c2.metric('Meses calendario',len(s)); c3.metric('Completitud mensual',f'{100*n/len(s):.1f} %' if len(s) else '—')

    st.caption('Solo meses calendario completos con registros diarios numéricos no negativos y sin marca de calidad. Las marcas originales siguen pendientes de interpretación. Sin relleno de faltantes.')

    if tendencias:

        from .tendencias import mann_kendall, pendiente_sen, mann_kendall_hamed_rao

        anual=anual_completo(s,'sum' if variable=='Precipitación' else 'mean')

        st.line_chart(anual.set_index('anio').valor,y_label='mm/año' if variable=='Precipitación' else unidad)

        if len(anual)>=10:

            mk=mann_kendall(anual.valor.to_numpy()); sen=pendiente_sen(anual.anio.to_numpy(),anual.valor.to_numpy()); hr=mann_kendall_hamed_rao(anual.anio.to_numpy(),anual.valor.to_numpy())

            from .chingaza_tendencias_ui import mostrar_resultados_tendencia

            mostrar_resultados_tendencia(mk, sen, hr, anual.anio, 'mm/año' if variable=='Precipitación' else unidad)

        else: st.info('Se requieren al menos 10 años completos para evaluar tendencias en este panel.')

        st.caption('Solo años con los doce meses válidos; caudal anual ponderado por días del mes.')

    else:

        fig=go.Figure(go.Scatter(x=s.fecha,y=s.valor,mode='lines',connectgaps=False,name=variable)); fig.update_layout(yaxis_title=unidad); st.plotly_chart(fig,width='stretch')

        reg=s.groupby(s.fecha.dt.month).valor.agg(['mean','count']).reindex(range(1,13)); st.subheader('Régimen mensual multianual'); st.bar_chart(reg['mean'],y_label=unidad); st.dataframe(reg.rename(columns={'mean':'Promedio','count':'Meses válidos'}),width='stretch')

        if variable=='Caudal' and n:

            q=s.valor.dropna().sort_values(ascending=False).reset_index(drop=True); exc=100*(q.index+1)/(len(q)+1)

            fig=go.Figure(go.Scatter(x=exc,y=q,mode='lines')); fig.update_layout(title='Curva de duración de caudales medios mensuales',xaxis_title='Excedencia (%)',yaxis_title='m³/s'); st.plotly_chart(fig,width='stretch'); st.caption('No equivale a una curva de duración diaria.')

        st.download_button('Descargar serie mensual seleccionada',s.to_csv(index=False,date_format='%Y-%m-%d').encode('utf-8-sig'),f'eaab_{cod}_mensual.csv','text/csv',key=f'chingaza_descarga_{variable}')



def clima():

    from .precipitacion_satelital import mostrar_precipitacion_satelital

    st.title('🌧️ Clima de Chingaza'); r=referencia(); st.caption(f'Referencia puntual PNN: {r["lat"]}, {r["lon"]}. No representa un promedio areal.')

    tab1,tab2,tab3,tab4,tab5=st.tabs(['NASA POWER','CHIRPS / IMERG / NASA','Precipitación EAAB','IDEAM','Comparación mensual'])

    with tab1:

        d=leer_nasa(); st.caption('NASA POWER AG · estimación de grilla. Solo meses completos por variable; no se publican series diarias.')

        if d.empty: st.info('NASA POWER pendiente de descarga. Ejecutar scripts/21_chingaza_satelital.py --fuente nasa_power.')

        else:

            col=st.selectbox('Variable NASA POWER',list(NASA_COLUMNAS),format_func=lambda x:NASA_COLUMNAS[x],key='chingaza_nasa_var'); st.line_chart(d.set_index('fecha')[col],y_label=NASA_COLUMNAS[col]); st.dataframe(climatologia_nasa(),hide_index=True,width='stretch'); st.download_button('Descargar NASA POWER mensual',d.to_csv(index=False,date_format='%Y-%m-%d').encode('utf-8-sig'),'nasa_power_chingaza_mensual.csv','text/csv')

    with tab2: mostrar_precipitacion_satelital('Chingaza')

    with tab3: observaciones('Precipitación')

    with tab4: mostrar_ideam()
    with tab5: mostrar_comparacion_precipitacion()



def mostrar(seccion):

    if seccion=='Isótopos': isotopos_chingaza()

    elif seccion=='Geología': geologia_chingaza()

    elif seccion=='Hidrogeología': hidrogeologia_chingaza()

    elif seccion=='Mapa y territorio': mapa()

    elif seccion=='Clima': clima()

    elif seccion=='Hidrología':

        st.title('💧 Hidrología superficial · Chingaza')

        # SIAMS_CHINGAZA_SWOT_COMPARTIDO

        from .swot import mostrar_gifs_swot, mostrar_tarjetas_swot

        tab_q, tab_swot = st.tabs(['Caudales EAAB', 'Embalse Chuza · SWOT'])

        with tab_q:

            observaciones('Caudal')

        with tab_swot:

            st.caption('Fuente: HydroWeb / SWOT. Recursos satelitales compartidos con Bogotá, no registros diarios del Acueducto.')

            mostrar_gifs_swot('Chingaza')

            mostrar_tarjetas_swot('Chingaza')

    elif seccion=='Estaciones y datos':

        st.title('Estaciones del proyecto Chingaza'); st.caption(FUENTE); st.dataframe(pd.read_csv(BASE/'eaab_estaciones.csv',dtype={'estacion':str}),hide_index=True,width='stretch'); st.caption('Verificación cartográfica de coordenadas EAAB pendiente.')

        st.subheader('Estaciones IDEAM')

        mostrar_inventario()

    elif seccion=='Homogeneidad (A1)':
        from .chingaza_tendencias_ui import mostrar_homogeneidad_chingaza
        st.title('Homogeneidad de series · Chingaza')
        mostrar_homogeneidad_chingaza()
    elif seccion=='Análisis de tendencias':

        from .chingaza_tendencias_ui import mostrar_tendencias_satelitales, mostrar_homogeneidad_chingaza

        from .chingaza_ideam import mostrar_ideam

        st.title('📈 Tendencias hidroclimáticas · Chingaza')

        teaab,tideam,tsat,tsnht=st.tabs(['EAAB','IDEAM','Productos satelitales','Homogeneidad · SNHT'])

        with teaab: observaciones(tendencias=True)

        with tideam: mostrar_ideam()

        with tsat: mostrar_tendencias_satelitales()

        with tsnht: mostrar_homogeneidad_chingaza()

        st.caption('Consulte GWSa y GGDI en Subsuelo y calidad del agua → Agua subterránea (GRACE).')

# SIAMS_CHINGAZA_GEOLOGIA_ESTUDIOS

_FUENTE_GEO_CHUZA = ('Universidad Nacional de Colombia (IEU) y Empresa de Acueducto, Alcantarillado y Aseo de Bogotá (EAB). '

    'Aspectos geoambientales sistema Chingaza. Fase I: Caracterización geológica, geoquímica y modelo estático de la cuenca del río Chuza. '

    'Noviembre de 2013. Convenio 9-07-26200-0766 de 2012.')

_FUENTE_HIDRO_CHUZA = ('GMAS S.A.S. y EAB-ESP. Productos 5 y 6 — Informe final: estudio geofísico para el desarrollo '

    'del modelo tridimensional en la cuenca del río Chuza, Fase II. Marzo de 2016. Contrato 2-24300-594-2015.')





def _figura_estudio_chuza(nombre, pie):

    ruta = BASE / 'geologia' / nombre

    if ruta.is_file():

        st.image(str(ruta), caption=pie, width='stretch')

    else:

        st.warning('No se encontró la figura de referencia del estudio.')





def geologia_chingaza():

    st.title('🪨 Geología · Chingaza')

    st.caption('Cuenca del río Chuza · Caracterización geológica y estructural')

    st.info('El alcance de los estudios es la cuenca del río Chuza y no la totalidad del PNN Chingaza. Las figuras son referencias documentales, no nuevas capas vectoriales.')

    mapa_tab, unidades_tab, fuentes_tab = st.tabs(['Mapa geológico', 'Litología y estructuras', 'Fuentes y alcance'])

    with mapa_tab:

        _figura_estudio_chuza('mapa_geologico_chuza.png', 'Fuente: Fase I, UNAL–EAB (2013), figura 1, p. 19. Mapa geológico y muestras petrográficas. Recorte del informe original.')

    with unidades_tab:

        st.subheader('Unidades y comportamiento del macizo rocoso')

        st.dataframe(pd.DataFrame([

            {'Unidad': 'Formación Une', 'Litología / rasgo': 'Areniscas cuarzosas con fuerte cementación silícea.', 'Interpretación': 'Baja porosidad primaria; las fracturas favorecen la circulación.'},

            {'Unidad': 'Formación Fómeque, miembro superior', 'Litología / rasgo': 'Lodolitas y niveles calcáreos; fracturamiento importante.', 'Interpretación': 'Posible acuífero por fracturas, según el estudio.'},

            {'Unidad': 'Fómeque inferior y Chipaque', 'Litología / rasgo': 'Predominio de rocas de grano fino.', 'Interpretación': 'La respuesta hidráulica depende de la deformación y discontinuidades.'},

            {'Unidad': 'Depósitos cuaternarios', 'Litología / rasgo': 'Sedimentos poco consolidados y heterogéneos.', 'Interpretación': 'Porosidad intergranular y almacenamiento temporal.'},

        ]), hide_index=True, width='stretch')

        st.markdown('**Geología estructural.** Las fallas pueden facilitar, limitar o redistribuir el flujo. La porosidad secundaria asociada a la red de fracturas resulta relevante frente a la baja porosidad primaria de varias unidades cretácicas.')

        st.caption('Síntesis: Fase I, pp. 220–221; Fase II, pp. 174–175.')

    with fuentes_tab:

        st.markdown(_FUENTE_GEO_CHUZA)

        st.markdown(_FUENTE_HIDRO_CHUZA)

        st.caption('El mapa no se ha digitalizado como capa SIG. No se asignan propiedades hidráulicas medidas a unidades sin ensayos específicos.')





def hidrogeologia_chingaza():

    st.title('💧 Hidrogeología · Chingaza')

    st.caption('Modelo hidrogeológico conceptual de la cuenca del río Chuza')

    modelo, unidades, alcance = st.tabs(['Modelo conceptual', 'Acuíferos y flujo', 'Alcance y fuentes'])

    with modelo:

        _figura_estudio_chuza('modelo_hidrogeologico_chuza.png', 'Fuente: GMAS–EAB (2016), Fase II, figura 17, p. 73. Modelo hidrogeológico conceptual; recorte del informe original.')

        st.markdown('La recarga se interpreta como infiltración desde suelo y vegetación hacia depósitos porosos y, dependiendo de la conexión entre discontinuidades, hacia unidades fracturadas. El estudio interpreta un flujo predominantemente subsuperficial.')

        st.caption('Fase II, pp. 72–73 y 173–175. No es un modelo numérico calibrado.')

    with unidades:

        st.subheader('Espesores interpretados mediante geofísica')

        a,b,c=st.columns(3)

        a.metric('Depósitos porosos', '4 a <20 m')

        b.metric('Une fracturado', '≈30 m')

        c.metric('Fómeque superior', '≈50 m')

        st.caption('Depósitos: espesor generalmente inferior a 20 m, mínimos de 4 m y casos excepcionales de hasta 50 m. Une y Fómeque: espesores promedio interpretados; no son profundidades al nivel freático. Fuente: Fase II, p. 175.')

        st.markdown('**Depósitos cuaternarios:** acuíferos detríticos libres; niveles finos pueden interrumpir el flujo vertical. **Roca fracturada:** la capacidad de transferencia depende de la densidad, apertura y conectividad de las fracturas. Las corrientes superficiales pueden constituir zonas de descarga local.')

        st.caption('Fuente: Fase II, pp. 174–175.')

    with alcance:

        st.markdown(_FUENTE_HIDRO_CHUZA)

        st.markdown(_FUENTE_GEO_CHUZA)

        st.warning('La cobertura geofísica fue insuficiente para construir un modelo tridimensional de toda la cuenca. La recarga neta requiere un balance hídrico y observaciones adicionales. No extrapolar los espesores a todo el parque.')

        st.caption('Fase II, pp. 73 y 173. GRACE/GGDI se consultan en el visor regional separado; no equivalen a niveles freáticos locales.')

# SIAMS_CHINGAZA_ISOTOPOS_MENSUALES

_FUENTE_ISOTOPOS_CHINGAZA = ('UNAL · Proyecto Chingaza, carpeta Isotopos. BASE_UNAL.xlsx, hojas Completo y Chingaza; '

    'pares isotópicos contrastados con BASE_UNAL(1).xlsx. Registros de 2023.')





def isotopos_chingaza():

    import plotly.express as px

    from .sedes_2026 import lmwl

    st.title('🔬 Hidrología isotópica · Chingaza')

    st.caption(_FUENTE_ISOTOPOS_CHINGAZA)

    ruta=BASE/'isotopos'/'lluvia_mensual.csv'

    if not ruta.is_file():

        st.info('La base mensual de totalizadores todavía no está disponible.')

        return

    d=pd.read_csv(ruta,dtype={'periodo':str}).sort_values(['periodo','totalizador'])

    st.caption('Mes nominal de la muestra, según las etiquetas de origen. No se supone que el intervalo de captación cubra exactamente todo el mes calendario. Las fechas de toma y laboratorio no se publican.')

    a,b,c=st.columns(3)

    a.metric('Totalizadores',d.totalizador.nunique()); b.metric('Meses con datos',d.periodo.nunique()); c.metric('Pares isotópicos',len(d))

    opciones=d[['totalizador','estacion']].drop_duplicates().sort_values('totalizador')

    nombres=opciones.set_index('totalizador').estacion.to_dict()

    elegidos=st.multiselect('Totalizadores',list(nombres),default=list(nombres),format_func=lambda k:f'{k} · {nombres[k]}',key='chingaza_iso_est')

    meses=sorted(d.periodo.unique())

    seleccion=st.select_slider('Meses reportados',options=meses,value=(meses[0],meses[-1]),key='chingaza_iso_periodo') if len(meses)>1 else (meses[0],meses[0])

    w=d[d.totalizador.isin(elegidos)&d.periodo.between(*seleccion)].copy()

    if w.empty:

        st.info('Selecciona al menos un totalizador con información en el periodo.')

        return

    diagrama, series, inventario, metodologia=st.tabs(['Diagrama isotópico','Evolución mensual','Estaciones y datos','Metodología y fuentes'])

    labels={'d18O':'δ¹⁸O (‰ VSMOW)','d2H':'δ²H (‰ VSMOW)','exceso_deuterio':'Exceso de deuterio (‰)','estacion':'Totalizador','periodo':'Mes reportado'}

    with diagrama:

        fig=px.scatter(w,x='d18O',y='d2H',color='estacion',hover_data=['periodo','altitud_m','exceso_deuterio'],labels=labels,height=500)

        xs=[float(w.d18O.min())-1,float(w.d18O.max())+1]

        fig.add_trace(go.Scatter(x=xs,y=[8*x+10 for x in xs],mode='lines',name='GMWL · Craig (1961)',line={'dash':'dash','color':'#888888'}))

        if len(w)>=5 and w.d18O.nunique()>1:

            a,b,n=lmwl(w)

            fig.add_trace(go.Scatter(x=xs,y=[a*x+b for x in xs],mode='lines',name='Ajuste descriptivo de la selección',line={'dash':'dot'}))

            st.markdown(f'**Ajuste exploratorio:** δ²H = {a:.2f}·δ¹⁸O {b:+.2f} ‰ · n = {n}')

        st.plotly_chart(fig,width='stretch')

        st.info('El ajuste utiliza mínimos cuadrados sin ponderación por precipitación. Seis meses de un solo año no permiten establecer una línea meteórica local climatológica definitiva ni cuantificar recarga.')

    with series:

        for variable in ('d18O','d2H','exceso_deuterio'):

            fig=px.line(w,x='periodo',y=variable,color='estacion',markers=True,labels=labels,height=330)

            fig.update_xaxes(type='category',categoryorder='array',categoryarray=meses)

            st.plotly_chart(fig,width='stretch')

    with inventario:

        st.dataframe(w[['totalizador','estacion','altitud_m']].drop_duplicates(),hide_index=True,width='stretch')

        st.dataframe(w[['periodo','totalizador','estacion','d18O','d2H','exceso_deuterio']].rename(columns=labels),hide_index=True,width='stretch')

        st.download_button('Descargar datos mensuales seleccionados (CSV)',w.to_csv(index=False).encode('utf-8-sig'),'chingaza_isotopos_lluvia_mensual.csv','text/csv',key='chingaza_iso_descarga')

    with metodologia:

        st.markdown('**δ¹⁸O y δ²H:** composición isotópica expresada en ‰ respecto a VSMOW. **Exceso de deuterio:** d = δ²H − 8·δ¹⁸O, recalculado a partir de los pares originales. La referencia global es δ²H = 8·δ¹⁸O + 10 (Craig, 1961).')

        st.markdown('**Alcance:** 18 pares de tres totalizadores de lluvia, mayo–octubre de 2023. No se aplicó interpolación, exclusión automática de valores extremos ni ponderación por volumen o precipitación; falta verificar protocolos de muestreo y control analítico.')

        st.markdown(_FUENTE_ISOTOPOS_CHINGAZA)

        st.caption('Craig, H. (1961). Isotopic Variations in Meteoric Waters. Science, 133(3465), 1702–1703.')

        st.info('El archivo de investigación también contiene 15 muestras superficiales y 6 clasificadas como subterráneas (principalmente filtraciones de infraestructura). Sus valores puntuales no forman parte de este producto público. Pendiente autorización específica y revisión de procedencia.')

# SIAMS_CHINGAZA_VALIDACION_MENSUAL

def mostrar_comparacion_precipitacion():
    from .chingaza_datos import comparar_precipitacion_mensual
    from .chingaza_ideam import cargar as cargar_ideam, FUENTE as FUENTE_IDEAM
    from .precipitacion_satelital_datos import cargar as cargar_sat
    import numpy as np
    st.subheader('Comparación mensual de precipitación observada y satelital')
    st.caption('NASA POWER AG · CHIRPS v3 Final · IMERG Final V07B. Productos del punto de referencia del PNN, no extraídos en cada estación. Comparación exploratoria, no validación espacial estricta.')
    fuente=st.radio('Fuente observada',['EAAB','IDEAM'],horizontal=True,key='ch_val_fuente')
    try:
        if fuente=='EAAB':
            d=leer_eaab(); est=pd.read_csv(BASE/'eaab_estaciones.csv',dtype={'estacion':str}); st.caption(FUENTE)
        else:
            est,_,d=cargar_ideam(); st.caption(FUENTE_IDEAM)
        sat,avisos=cargar_sat('chingaza')
        ref=referencia()
    except (OSError,ValueError,KeyError) as exc:
        st.warning(f'No fue posible cargar la información: {exc}'); return
    d=d[d.variable.eq('Precipitación') & d.valor.notna()].copy()
    if 'etiqueta' in d: d=d[d.etiqueta.eq('PTPM_CON')]
    if 'unidad' in d: d=d[d.unidad.eq('mm/mes')]
    if d.empty or sat.empty:
        st.info('No hay series mensuales comparables disponibles.'); return
    if avisos:
        with st.expander('Disponibilidad de fuentes'):
            for nombre,aviso in avisos.items(): st.caption(f'{nombre}: {aviso}')
    nombres=est.drop_duplicates('estacion').set_index('estacion').nombre.to_dict()
    cod=st.selectbox('Estación de referencia',sorted(d.estacion.unique(),key=lambda c:nombres.get(c,c)),format_func=lambda c:f'{nombres.get(c,c)} · {c}',key='ch_val_est_'+fuente)
    meta=est[est.estacion.eq(cod)].iloc[0]
    lat,lon=pd.to_numeric(meta.get('latitud', np.nan),errors='coerce'),pd.to_numeric(meta.get('longitud', np.nan),errors='coerce')
    if np.isfinite(lat) and np.isfinite(lon):
        phi1,phi2=np.radians([lat,ref['lat']]); dl=np.radians(lon-ref['lon']); dp=phi1-phi2
        dist=2*6371.0088*np.arcsin(np.sqrt(np.clip(np.sin(dp/2)**2+np.cos(phi1)*np.cos(phi2)*np.sin(dl/2)**2,0,1)))
        st.caption(f'Distancia estación–punto de referencia: {dist:.1f} km (geodésica aproximada, no distancia a centros de píxel).')
    else: st.caption('Distancia no disponible: coordenadas de esta estación no incorporadas al inventario mensual.')
    obs=d[d.estacion.eq(cod)].set_index('fecha').valor.rename('Observada').sort_index()
    if obs.index.has_duplicates:
        st.warning('La estación presenta meses duplicados; revise el inventario.');return
    seleccion=st.multiselect('Productos a comparar',list(sat.columns),default=list(sat.columns),key='ch_val_productos')
    if not seleccion: return
    tabla=pd.concat([obs,sat[seleccion]],axis=1).sort_index()
    tabla=tabla.where(np.isfinite(tabla)&tabla.ge(0))
    posibles=tabla.Observada.notna()&tabla[seleccion].notna().any(axis=1)
    if not posibles.any(): st.info('No hay meses comunes.');return
    fechas=tabla.index[posibles]; a,b=int(fechas.year.min()),int(fechas.year.max())
    ini,fin=st.slider('Periodo de comparación (años)',a,b,(a,b),key='ch_val_periodo_'+fuente+cod) if a<b else (a,b)
    tabla=tabla.loc[f'{ini}-01':f'{fin}-12']
    comun=st.checkbox('Usar exactamente los mismos meses para todos los productos',value=True,key='ch_val_comunes')
    if comun: tabla=tabla.where(tabla.notna().all(axis=1),axis=0)
    met=comparar_precipitacion_mensual(tabla)
    if met.empty: st.info('No hay coincidencias para esta selección. Pruebe otro periodo o comparación por pares.');return
    st.line_chart(tabla,y_label='Precipitación (mm/mes)')
    st.dataframe(met.round(3),hide_index=True,width='stretch')
    if (met['Meses comunes']<24).any(): st.warning('Al menos un producto tiene menos de 24 meses comunes; las métricas son especialmente sensibles a la muestra.')
    st.caption('Sesgo y PBIAS positivos indican sobreestimación (satélite − observada). MAE y RMSE ideales: 0. r, NSE y KGE 2009 ideales: 1. Un resultado vacío indica que la métrica no está definida; no se sustituye por cero.')
    for producto in seleccion:
        par=tabla[['Observada',producto]].dropna()
        if par.empty: continue
        with st.expander(f'Dispersión y climatología pareada · {producto}'):
            fig=go.Figure(go.Scatter(x=par.Observada,y=par[producto],mode='markers',name=producto))
            lim=float(par.max().max()); fig.add_trace(go.Scatter(x=[0,lim],y=[0,lim],mode='lines',name='1:1',line=dict(dash='dash')))
            fig.update_layout(xaxis_title='Observada (mm/mes)',yaxis_title=producto+' (mm/mes)',height=390); st.plotly_chart(fig,width='stretch',key='ch_val_scatter_'+producto)
            regimen=par.groupby(par.index.month).mean().reindex(range(1,13)); st.line_chart(regimen,y_label='mm/mes');st.caption('Climatología calculada exclusivamente sobre meses pareados.')
    with st.expander('Alcance metodológico'):
        st.markdown('**NSE:** 1 − Σ(sim−obs)² / Σ(obs−media obs)². **KGE 2009:** 1 − √[(r−1)² + (σsim/σobs−1)² + (μsim/μobs−1)²]. No se calculan POD ni FAR de eventos diarios a partir de totales mensuales. La validación espacial requiere extraer cada producto en la ubicación de la estación y considerar su resolución y representatividad.')
    datos=tabla.dropna(how='all').rename_axis('fecha').reset_index().assign(estacion=cod,fuente_observada=fuente,lat_referencia=ref['lat'],lon_referencia=ref['lon'])
    st.download_button('Descargar comparación mensual',datos.to_csv(index=False,date_format='%Y-%m').encode('utf-8-sig'),'chingaza_comparacion_mensual.csv','text/csv',key='ch_val_desc')
    st.download_button('Descargar métricas',met.assign(estacion=cod,fuente_observada=fuente,soporte='comun' if comun else 'pares').to_csv(index=False).encode('utf-8-sig'),'chingaza_metricas_precipitacion.csv','text/csv',key='ch_val_metricas')
