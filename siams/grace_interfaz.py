"""Observatorio público de Leticia · SIAMS.

Integra el material PÚBLICO del Explorador Leticia compartido por la profesora
Piña. Preserva las series GRACE/GLDAS del semillero; no accede a archivos
privados ni a coordenadas instrumentales precisas. No duplica el menú general.
"""
from __future__ import annotations

from pathlib import Path
import os
import json
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from .grace_datos import RAIZ, DATOS_PUBLICOS, cargar, leer_csv_seguro
from .grace_analisis import (
    FUENTES_DIARIAS, validar_lluvia_diaria, indicadores_diarios,
    mensual_emparejado, series_pozos_publicas, lag_lluvia_columna, anual_minimos,
    coordenadas_piper, calidad_horaria, correlacion_lluvia_cambio, preparar_numae_diario,
)

VERDE = '#18796F'
AZUL = '#4284B3'
AMBAR = '#C49356'
MORADO = '#8B79B1'
GRIS = '#7C8996'
ROJO = '#BD675E'
ETIQUETAS_LLUVIA = {
    'CHIRPS v3': 'chirps_v3_sat_mm',
    'IMERG Final V07': 'imerg_final_mm',
    'IMERG Late V07': 'imerg_late_mm',
    'ERA5 (Open-Meteo)': 'era5_precip_mm',
}


def _grafico(fig: go.Figure, eje_y: str, alto: int=410) -> go.Figure:
    fig.update_layout(
        height=alto, margin=dict(l=10,r=14,t=33,b=46),
        paper_bgcolor='rgba(0,0,0,0)',plot_bgcolor='rgba(0,0,0,0)',
        hovermode='x unified',font=dict(size=12),
        xaxis=dict(title=None, showgrid=False),
        yaxis=dict(title=eje_y,gridcolor='rgba(130,142,150,.16)',zeroline=False),
        legend=dict(orientation='h',x=0,y=-0.25),
    )
    return fig


def _plot(fig: go.Figure, key: str, eje: str, alto: int=410) -> None:
    st.plotly_chart(_grafico(fig,eje,alto),width='stretch',key=f'siams_public_{key}')


def _datos(nombre: str) -> pd.DataFrame:
    try:
        return cargar(nombre)
    except (ValueError, OSError, pd.errors.ParserError) as exc:
        st.warning(f'No se pudo leer {nombre}: {exc}')
        return pd.DataFrame()


def _numerico(d: pd.DataFrame, campos: list[str]) -> pd.DataFrame:
    r=d.copy()
    for c in campos:
        if c in r:r[c]=pd.to_numeric(r[c],errors='coerce')
    return r


def _tiempo(d: pd.DataFrame, campo: str='fecha') -> pd.DataFrame:
    r=d.copy()
    if campo in r:r[campo]=pd.to_datetime(r[campo],errors='coerce')
    return r.dropna(subset=[campo])


def _aviso() -> None:
    st.caption('Datos de la **versión pública** del Explorador Leticia (taller 2026). '
               'Se conservan períodos, unidades y vacíos. Los sitios sensibles utilizan '
               'identificadores públicos y coordenadas redondeadas; el análisis no confirma '
               'horarios de operación de bombas ni sustituye verificación de campo.')


def _grace_profesora() -> pd.DataFrame:
    ruta=RAIZ/'data/processed/grace/leticia/GWSA_A_B_sites_Leticia.csv'
    if not ruta.is_file():return pd.DataFrame()
    try:
        d=pd.read_csv(ruta,low_memory=False)
        if not {'nominal_month','GWSA_B_standard_cm','GWSA_A_original_cm'}.issubset(d):
            return pd.DataFrame()
        d['mes']=pd.to_datetime(d.nominal_month,errors='coerce').dt.to_period('M').dt.to_timestamp()
        return _numerico(d,['GWSA_B_standard_cm','GWSA_A_original_cm','Zenodo_GWSA_cm'])
    except (OSError,ValueError,pd.errors.ParserError):return pd.DataFrame()


def _rango_rio_publico() -> pd.DataFrame:
    ideam=_datos('rio_diario.csv')
    ana=_datos('ana_diario.csv')
    if ideam.empty:return pd.DataFrame()
    i=_numerico(_tiempo(ideam),['nivel_m'])[['fecha','nivel_m']]
    a=_numerico(_tiempo(ana),['cota_m'])[['fecha','cota_m']] if not ana.empty else pd.DataFrame(columns=['fecha','cota_m'])
    return i.merge(a,on='fecha',how='outer').sort_values('fecha')


def _portada() -> None:
    st.markdown('''<style>
    .siams-le-hero {background:linear-gradient(120deg,#123D42,#176E67 60%,#276883);
      border-radius:17px;padding:21px 24px;margin:10px 0 16px;color:#fff}
    .siams-le-hero h2{color:#fff!important;margin:4px 0 8px!important;
      font-size:1.55rem!important;line-height:1.25!important}
    .siams-le-hero p{margin:0;color:#e6f7f4!important;line-height:1.6;
      font-size:.91rem;max-width:850px}
    .siams-le-eye{font-size:.73rem;letter-spacing:.11em;color:#bbe9e2;font-weight:700}
    </style>
    <div class="siams-le-hero"><div class="siams-le-eye">SIAMS · SEDE AMAZONIA</div>
    <h2>Agua subterránea y monitoreo · Leticia</h2>
    <p>Relaciones entre pozos, lluvias, río Amazonas y almacenamiento GRACE.
    Cada señal conserva su escala, su procedencia y sus límites de interpretación.</p>
    </div>''',unsafe_allow_html=True)


def _panorama() -> None:
    st.subheader('Panorama del monitoreo')
    trans=series_pozos_publicas(_datos('transductores_diarios_publicos.csv'))
    g=_grace_profesora(); lluvia=_datos('lluvia_ideam_diaria.csv')
    rio=_datos('rio_diario.csv')
    c1,c2,c3,c4=st.columns(4)
    c1.metric('Días de transductores',int(trans.fecha.nunique()) if not trans.empty else '—')
    c2.metric('Puntos con serie diaria',int(trans.pozo.nunique()) if not trans.empty else '—')
    c3.metric('Días IDEAM disponibles',len(lluvia) if not lluvia.empty else '—')
    c4.metric('Meses GRACE procesados',int(g.GWSA_B_standard_cm.notna().sum()) if not g.empty else '—')
    st.markdown('#### Del registro de campo al contexto regional')
    st.markdown('Las **sondas** miden columna de agua sobre un sensor; el **río** registra '
                'nivel respecto a su propia mira, y **GRACE** estima una anomalía regional '
                'de almacenamiento. Son señales relacionadas, pero no intercambiables.')
    gpub=_datos('grace.csv')
    if not gpub.empty:
        gp=_numerico(_tiempo(gpub,'mes'),['gwsa_cm','twsa_cm']).sort_values('mes')
        fig=go.Figure()
        fig.add_trace(go.Scatter(x=gp.mes,y=gp.gwsa_cm,mode='lines',name='GWSa · método B (cm)',
                                 line=dict(color=VERDE,width=2.6),connectgaps=False))
        fig.add_hline(y=0,line=dict(color=GRIS,dash='dot'))
        _plot(fig,'panorama_grace','GWSa regional (cm equivalentes)',340)
        st.caption('Serie del explorador público: GRACE/GLDAS y referencia 2004–2009. '
                   'Las brechas del satélite quedan sin interpolar.')
    st.info('**Cómo navegar:** «Niveles y bombeo» contiene las gráficas de pozos y lluvia. '
            '«GRACE y río» compara almacenamiento y régimen fluvial. «Validación de lluvia» '
            'calcula sesgo, KGE, POD, FAR y CSI cuando existen pares diarios suficientes.')


def _niveles() -> None:
    st.subheader('Niveles de agua y señales de bombeo')
    trans=series_pozos_publicas(_datos('transductores_diarios_publicos.csv'))
    if trans.empty:
        st.error('No se encontraron las series diarias públicas de transductores.'); return
    inventario=RAIZ/'data/processed/niveles/niveles_leticia.csv'
    if inventario.is_file():
        try:
            raw=pd.read_csv(inventario,usecols=['fecha','calidad','pozo_id'],low_memory=False)
            total=len(raw); num=raw.pozo_id.nunique(); frac=100*raw.calidad.fillna('sin dato').ne('ok').mean()
            a,b,c=st.columns(3)
            a.metric('Registros del semillero',f'{total:,}'.replace(',','.'))
            b.metric('Puntos registrados',num)
            c.metric('Marcados para revisión',f'{frac:.1f} %')
        except (ValueError,OSError,pd.errors.ParserError):pass
    st.caption('Las cifras de registros provienen de la serie procesada del semillero; '
               'las gráficas siguientes usan exclusivamente las **series publicadas** en el explorador.')
    sitios=trans.pozo.dropna().unique().tolist()
    sitio=st.selectbox('Punto de observación',sitios,key='leticia_public_niveles_punto')
    d=trans.loc[trans.pozo.eq(sitio)].sort_values('fecha').copy()
    d=d.loc[d.fecha.ge(d.fecha.min())]
    a,b,c=st.columns(3)
    a.metric('Días con registros',int(d.natural.notna().sum()))
    b.metric('Columna mediana (m)',f'{d.natural.median():.2f}' if d.natural.notna().any() else '—')
    c.metric('Días con indicios de bombeo',int(d.frac_bombeo.gt(0).sum()) if d.frac_bombeo.notna().any() else '—')
    fig=go.Figure()
    fig.add_trace(go.Scatter(x=d.fecha,y=d.natural,mode='lines+markers',
                             name='Columna de madrugada / nivel natural (m)',
                             line=dict(color=VERDE,width=2.7),marker=dict(size=4),connectgaps=False))
    if d.max_diario.notna().sum():
        fig.add_trace(go.Scatter(x=d.fecha,y=d.max_diario,mode='lines',
            name='Columna máxima diaria (m)',line=dict(color=AMBAR,dash='dot'),connectgaps=False))
    _plot(fig,'pozo_columna','Columna de agua sobre sensor (m)',430)
    st.caption('Columna de agua sobre el sensor, **no profundidad ni cota absoluta del nivel**. '
               'La madrugada y el máximo diario provienen del procesamiento del explorador; '
               'las separaciones temporales sin lectura no se rellenan.')
    if d.frac_bombeo.notna().sum():
        st.markdown('#### Indicios instrumentales de bombeo')
        b=go.Figure()
        b.add_trace(go.Bar(x=d.fecha,y=100*d.frac_bombeo,name='Posible bombeo (%)',marker_color=AMBAR))
        if d.frac_seco.notna().sum():
            b.add_trace(go.Scatter(x=d.fecha,y=100*d.frac_seco,name='Sensor posiblemente al aire (%)',
                                   line=dict(color=ROJO,width=2),connectgaps=False))
        _plot(b,'bombeo_dias','Fracción diaria de registros (%)',350)
        st.caption('Las fracciones corresponden a criterios del explorador, no a un registro '
                   'verificado de encendido de la bomba. No equivalen a horas exactas de operación.')
    lluvia_i=_datos('lluvia_ideam_diaria.csv'); lluvias_s=_datos('lluvia_satelital_diaria.csv')
    if not lluvia_i.empty and not lluvias_s.empty:
        st.markdown('#### ¿Cómo responde el pozo a la lluvia?')
        fuente=st.selectbox('Fuente de lluvia', ['IDEAM (aeropuerto)']+list(ETIQUETAS_LLUVIA),
                            key='leticia_lluvia_fuente_niveles')
        if fuente.startswith('IDEAM'):
            x=_numerico(_tiempo(lluvia_i),['mm','pct'])
            x=x.loc[x.pct.ge(75)][['fecha','mm']].rename(columns={'mm':'lluvia'})
        else:
            col=ETIQUETAS_LLUVIA[fuente]
            x=_numerico(_tiempo(lluvias_s),[col])[['fecha',col]].rename(columns={col:'lluvia'})
        z=d.merge(x,on='fecha',how='left')
        f=go.Figure()
        f.add_trace(go.Bar(x=z.fecha,y=z.lluvia,name='Lluvia diaria (mm)',marker_color='rgba(66,132,179,.48)'))
        f.add_trace(go.Scatter(x=z.fecha,y=z.natural,name='Columna natural (m)',
                              line=dict(color=VERDE,width=2.6),yaxis='y2',connectgaps=False))
        f.update_layout(yaxis=dict(title='Precipitación (mm/día)'),
                        yaxis2=dict(title='Columna sobre sensor (m)',side='right',overlaying='y'))
        _plot(f,'lluvia_columna','Lluvia (mm/día)',440)
        lag=lag_lluvia_columna(z,'lluvia',max_desfase=7,min_pares=25)
        if lag.r.notna().any():
            with st.expander('Correlaciones exploratorias de 0 a 7 días'):
                t=go.Figure(go.Bar(x=lag['Desfase (días)'],y=lag.r,
                                   marker_color=AZUL,text=lag.Pares,textposition='outside'))
                _plot(t,'lag_lluvia_pozo','Correlación Pearson (r)',320)
                st.caption('r[lluvia(t-k), cambio de columna(t)]. Se exige 25 pares como mínimo. '
                           'No identifica por sí solo recarga del acuífero.')
        else:
            st.caption('No hay suficientes pares diarios comparables para estimar un desfase confiable.')
    st.markdown('#### Lecturas manuales del pozo UNAL')
    manual=_datos('pozo_unal_manual.csv')
    if not manual.empty:
        m=_numerico(_tiempo(manual,'fechahora'),['prof'])
        fig=go.Figure(go.Scatter(x=m.fechahora,y=m.prof,mode='markers+lines',
                                marker=dict(color=AZUL,size=7),line=dict(color=AZUL,width=1),
                                name='Profundidad al agua'))
        fig.update_yaxes(autorange='reversed')
        _plot(fig,'manual_unal','Profundidad bajo boca del pozo (m)',355)
        st.caption('Mediciones manuales del pozo UNAL. Eje vertical invertido: más abajo = mayor profundidad. '
                   'El conjunto público ya excluye registros ilegibles de la hoja original.')
    st.markdown('#### Río Amazonas: contexto, no equivalencia de cotas')
    _comparacion_rio_niveles(d)
    st.info('**Referencia de Numae:** la configuración SIAMS de noviembre usa 17 m de profundidad '
            'de sensor y una cota de terreno estimada por DEM. No se presentan como '
            'levantamiento topográfico confirmado; aquí se representa columna sobre sensor.')


def _comparacion_rio_niveles(d: pd.DataFrame) -> None:
    rio=_numerico(_tiempo(_datos('rio_diario.csv')),['nivel_m'])
    if rio.empty:return
    r=d[['fecha','natural']].merge(rio[['fecha','nivel_m']],on='fecha',how='inner').dropna()
    if len(r)<8:
        st.caption('No hay suficientes fechas comunes para comparar visualmente las variaciones de pozo y río.')
        return
    # Anomalía respecto a la media del período estrictamente compartido.
    r['Pozo Δm']=r.natural-r.natural.mean()
    r['Río Δm']=r.nivel_m-r.nivel_m.mean()
    f=go.Figure()
    f.add_trace(go.Scatter(x=r.fecha,y=r['Pozo Δm'],mode='lines',
                           name='Columna del pozo · Δ (m)',line=dict(color=VERDE,width=2.6)))
    f.add_trace(go.Scatter(x=r.fecha,y=r['Río Δm'],mode='lines',
                           name='Río IDEAM · Δ (m)',line=dict(color=AZUL,width=2.2)))
    _plot(f,'pozo_rio','Desviación respecto a la media común (m)',340)
    st.caption(f'{len(r)} fechas comunes; se resta la media de cada serie en ese período. '
               'No se comparan niveles absolutos ni se estima una conexión hidráulica causal.')


def _grace_rio() -> None:
    st.subheader('GRACE/GLDAS y dinámica del río Amazonas')
    publico=_datos('grace.csv'); profesor=_grace_profesora()
    if publico.empty:return
    d=_numerico(_tiempo(publico,'mes'),['twsa_cm','smsa_cm','gwsa_cm','gwsa_zenodo_romero_pina_2025_cm'])
    d=d.sort_values('mes')
    st.caption('Se utiliza el método B del explorador como referencia para sus componentes. '
               'Si existe, la serie A/B procesada de SIAMS se conserva en paralelo.')
    opciones={'GWSa B del explorador':'gwsa_cm','TWSa (almacenamiento total)':'twsa_cm',
              'SMsa (humedad del suelo)':'smsa_cm',
              'Referencia Zenodo · Romero y Piña':'gwsa_zenodo_romero_pina_2025_cm'}
    elegido=st.selectbox('Serie principal',list(opciones),key='leticia_public_grace_serie')
    mostrar_rio=st.checkbox('Superponer anomalía del río (eje derecho)',value=True,
                             key='leticia_public_grace_con_rio')
    fig=go.Figure(go.Scatter(x=d.mes,y=d[opciones[elegido]],mode='lines',
                             name=elegido,line=dict(color=VERDE,width=2.5),connectgaps=False))
    if mostrar_rio:
        r=_numerico(_tiempo(_datos('rio_mensual.csv'),'mes'),['anom_cm'])
        if not r.empty:
            fig.add_trace(go.Scatter(x=r.mes,y=r.anom_cm,mode='lines',name='Río · anomalía (cm de nivel)',
                        line=dict(color=AZUL,width=1.7,dash='dot'),connectgaps=False,yaxis='y2'))
            fig.update_layout(yaxis2=dict(title='Anomalía del nivel del río (cm)',
                              overlaying='y',side='right'))
    fig.add_hline(y=0,line_color='rgba(128,128,128,.5)',line_dash='dot')
    _plot(fig,'grace_principal','Anomalía GRACE (cm equivalentes)',440)
    st.caption('GRACE: anomalías de almacenamiento regional, no niveles de pozos. '
               'El río se muestra en un eje distinto por la diferencia de significado físico. '
               'En la Amazonía la señal GWSa puede incluir agua superficial que GLDAS no separa.')
    if not profesor.empty:
        with st.expander('Comparación de métodos A/B que conserva la profesora'):
            p=profesor.sort_values('mes')
            f=go.Figure()
            for c,name,color in [('GWSA_B_standard_cm','B · estándar',VERDE),
                                  ('GWSA_A_original_cm','A · serie histórica',AMBAR)]:
                f.add_trace(go.Scatter(x=p.mes,y=p[c],mode='lines',connectgaps=False,
                                       name=name,line=dict(color=color,width=2.1)))
            _plot(f,'metodos_ab','GWSa (cm equivalentes)',350)
            st.caption('Los métodos no se empalman. Conservamos los cálculos del semillero y sus metadatos.')
    st.markdown('#### Ciclo medio por mes calendario')
    cyc=d.assign(mes_num=d.mes.dt.month).groupby('mes_num')[['gwsa_cm','twsa_cm','smsa_cm']].mean()
    fig=go.Figure()
    for c,name,color in [('gwsa_cm','GWSa',VERDE),('twsa_cm','TWSa',AZUL),
                         ('smsa_cm','SMsa',AMBAR)]:
        fig.add_trace(go.Scatter(x=cyc.index,y=cyc[c],name=name,mode='lines+markers',
                                 line=dict(color=color,width=2)))
    fig.update_xaxes(dtick=1,title='Mes del año')
    _plot(fig,'ciclo_grace','Anomalía media por mes (cm equivalentes)',340)
    st.caption('Media de todos los meses con datos; no equivale a una climatología de estaciones.')
    st.markdown('#### Mínimos anuales en años secos')
    rio=_datos('rio_mensual.csv')
    tabla=anual_minimos(d,rio)
    if not tabla.empty:
        tabla=tabla.loc[tabla.año.ge(2002)].copy()
        fig=go.Figure(go.Scatter(x=tabla.año,y=tabla.gwsa_min_cm,
                                name='Mínimo GWSa observado',mode='lines+markers',
                                line=dict(color=VERDE,width=2)))
        fig.update_xaxes(dtick=2,title='Año')
        _plot(fig,'minimos','Mínimo observado GWSa (cm)',335)
        st.caption('Los años con menos de 12 meses no se comparan como años completos. '
                   'El conteo de meses con río durante agosto–octubre se muestra en la tabla.')
        with st.expander('Tabla anual, meses disponibles y descarga'):
            st.dataframe(tabla,width='stretch',hide_index=True)
            st.download_button('Descargar mínimos anuales',tabla.to_csv(index=False).encode('utf-8-sig'),
                               'siams_leticia_minimos_grace_rio.csv','text/csv',
                               key='leticia_public_descarga_minimos')
    st.markdown('#### Estaciones IDEAM Leticia y ANA Tabatinga')
    rio=_rango_rio_publico()
    if not rio.empty:
        f=go.Figure()
        f.add_trace(go.Scatter(x=rio.fecha,y=rio.nivel_m,mode='lines',name='IDEAM · nivel (m)',
                               line=dict(color=AZUL,width=2.1),connectgaps=False))
        f.add_trace(go.Scatter(x=rio.fecha,y=rio.cota_m,mode='lines',
                               name='ANA · cota de referencia (m)',line=dict(color=AMBAR,width=2.1),
                               yaxis='y2',connectgaps=False))
        f.update_layout(yaxis2=dict(title='ANA Tabatinga · referencia propia (m)',overlaying='y',side='right'))
        _plot(f,'ana_ideam','IDEAM · nivel sobre mira (m)',360)
        st.caption('No se restan ni equiparan directamente ambas cotas: los ceros hidrométricos son distintos.')


def _lluvia() -> None:
    st.subheader('Validación diaria: IDEAM frente a satélites')
    i=_datos('lluvia_ideam_diaria.csv'); s=_datos('lluvia_satelital_diaria.csv')
    if i.empty or s.empty:
        st.error('Faltan los datos públicos de lluvia para comparar.');return
    c1,c2,c3=st.columns([1.1,1.1,1])
    with c1:producto=st.selectbox('Producto',list(ETIQUETAS_LLUVIA),key='leticia_public_producto')
    with c2:cobertura=st.selectbox('Completitud mínima IDEAM',[75,90],
                                 format_func=lambda x:f'{x} %',key='leticia_public_cobertura')
    with c3:umbral=st.number_input('Evento lluvia (mm/día)',min_value=0.1,max_value=50.,
                                   value=1.,step=0.5,key='leticia_public_umbral')
    pares=validar_lluvia_diaria(i,s,float(cobertura))
    c=ETIQUETAS_LLUVIA[producto]
    pares=pares.loc[pares[c].notna() & pares[c].ge(0)].copy()
    m=indicadores_diarios(pares.IDEAM_mm,pares[c],umbral) if not pares.empty else indicadores_diarios(pd.Series(dtype=float),pd.Series(dtype=float),umbral)
    ca,cb,cc,cd=st.columns(4)
    ca.metric('Días comparables',m['n']);cb.metric('Sesgo (mm/día)',f"{m['sesgo']:+.2f}" if np.isfinite(m['sesgo']) else '—')
    cc.metric('KGE',f"{m['kge']:.2f}" if np.isfinite(m['kge']) else '—')
    cd.metric('RMSE (mm/día)',f"{m['rmse']:.2f}" if np.isfinite(m['rmse']) else '—')
    if pares.empty:
        st.warning('El producto elegido no tiene fechas simultáneas con IDEAM y ese control de calidad.');return
    st.markdown('#### Comparación diaria')
    gra=pares.tail(365)
    f=go.Figure()
    f.add_trace(go.Bar(x=gra.fecha,y=gra.IDEAM_mm,name='IDEAM',marker_color=AZUL))
    f.add_trace(go.Scatter(x=gra.fecha,y=gra[c],mode='lines',name=producto,
                           line=dict(color=VERDE,width=1.9),connectgaps=False))
    _plot(f,'validacion_diaria','Precipitación (mm/día)',355)
    st.caption('Se muestran como máximo los últimos 365 días coincidentes; todos los pares disponibles '
               'se usan en las métricas. IDEAM: días con cobertura suficiente, ajuste horario del proyecto.')
    st.markdown('#### Detección de días de lluvia')
    a,b,cc=st.columns(3)
    a.metric('POD',f"{100*m['POD']:.1f} %" if np.isfinite(m['POD']) else '—')
    b.metric('FAR',f"{100*m['FAR']:.1f} %" if np.isfinite(m['FAR']) else '—')
    cc.metric('CSI',f"{100*m['CSI']:.1f} %" if np.isfinite(m['CSI']) else '—')
    st.caption(f"Umbral ≥ {umbral:g} mm/día. Aciertos: {m['aciertos']}; omisiones: {m['omisiones']}; "
               f"falsas alarmas: {m['falsas_alarmas']}. FAR es la proporción de predicciones "
               'de lluvia que fueron falsas, no la tasa de falsos positivos.')
    st.markdown('#### Acumulados mensuales emparejados')
    mensual=mensual_emparejado(pares,c,minimo_dias=20)
    if mensual.empty:
        st.info('No hay meses con 20 días simultáneamente válidos para este producto.')
    else:
        f=go.Figure()
        f.add_trace(go.Bar(x=mensual.mes,y=mensual.IDEAM_mm,name='IDEAM (días comunes)',marker_color=AZUL))
        f.add_trace(go.Bar(x=mensual.mes,y=mensual.Producto_mm,name=f'{producto} (días comunes)',
                           marker_color=VERDE))
        f.update_layout(barmode='group')
        _plot(f,'validacion_mensual','Lluvia acumulada en días comunes (mm)',365)
        st.caption('Se suman ambos productos únicamente durante los mismos días con observación. '
                   'Cada mes exige al menos 20 días emparejados; los totales pueden ser menores que '
                   'un acumulado de mes calendario completo.')
    with st.expander('Comparar los cuatro productos con los mismos criterios'):
        filas=[]
        sin_filtro=validar_lluvia_diaria(i,s,float(cobertura))
        for n,k in ETIQUETAS_LLUVIA.items():
            r=indicadores_diarios(sin_filtro.IDEAM_mm,sin_filtro[k],umbral)
            filas.append({'Producto':n,'Pares':r['n'],'Sesgo mm/d':r['sesgo'],
                          'RMSE mm/d':r['rmse'],'r':r['pearson'],'KGE':r['kge'],
                          'POD':r['POD'],'FAR':r['FAR'],'CSI':r['CSI']})
        t=pd.DataFrame(filas)
        st.dataframe(t,width='stretch',hide_index=True)
        st.download_button('Descargar validación diaria (resumen)',t.to_csv(index=False).encode('utf-8-sig'),
                           'SIAMS_leticia_validacion_diaria.csv','text/csv',
                           key='leticia_public_descarga_val')
    st.markdown('#### Régimen medio mensual satelital')
    sm=_datos('sat_mensual.csv')
    if not sm.empty:
        sm=_numerico(_tiempo(sm,'mes'),['chirps_v2_mm','chirps_v3_mm','imerg_final_mm'])
        sm=sm.loc[sm.mes.dt.year.between(2001,2020)]
        clima=sm.groupby(sm.mes.dt.month)[['chirps_v2_mm','chirps_v3_mm','imerg_final_mm']].mean()
        f=go.Figure()
        for k,n,color in [('chirps_v2_mm','CHIRPS v2',AMBAR),
                          ('chirps_v3_mm','CHIRPS v3',VERDE),
                          ('imerg_final_mm','IMERG Final',AZUL)]:
            f.add_trace(go.Scatter(x=clima.index,y=clima[k],mode='lines+markers',
                                   name=n,line=dict(color=color,width=2)))
        f.update_xaxes(dtick=1,title='Mes')
        _plot(f,'clima_lluvia','Lluvia media mensual 2001–2020 (mm)',350)
        st.caption('Climatología del píxel de Leticia; no es una validación contra estación IDEAM.')
    st.info('**Precaución:** distintos productos definen el día con distinta referencia horaria. '
            'La coincidencia diaria es aproximada si las ventanas UTC/local difieren; '
            'el ajuste de horarios IDEAM procede del taller, no del satélite.')


def _calidad() -> None:
    st.subheader('Calidad del agua e hidroquímica')
    d=_datos('calidad_muestras_publicas.csv')
    if d.empty:
        st.warning('No están disponibles las muestras públicas del explorador.');return
    d=_numerico(d,['irca_min','irca_max','cobertura','ph','ce','no3_mg',
                   'cat_ca_pct','cat_mg_pct','cat_nak_pct','an_hco3_pct','an_so4_pct','an_cl_pct'])
    grupo=st.selectbox('Campaña / laboratorio',sorted(d.grupo.dropna().unique()),key='leticia_public_calidad_grupo')
    q=d.loc[d.grupo.eq(grupo)].copy().sort_values('irca_min',ascending=False)
    a,b,c=st.columns(3)
    a.metric('Muestras',len(q))
    b.metric('Mediana IRCA mínimo',f'{q.irca_min.median():.1f} %' if len(q) else '—')
    c.metric('Cobertura de puntaje (mediana)',f'{q.cobertura.median():.0f} %' if len(q) else '—')
    st.markdown('#### IRCA del agua cruda por muestra')
    elegir=st.slider('Muestras a visualizar (ordenadas por IRCA)',min_value=5,
                     max_value=max(5,len(q)),value=min(20,len(q)),
                     key='leticia_public_calidad_n') if len(q)>=5 else len(q)
    t=q.head(elegir)
    f=go.Figure()
    f.add_trace(go.Bar(y=t.punto,x=t.irca_min,orientation='h',name='IRCA mínimo',marker_color=VERDE))
    f.add_trace(go.Bar(y=t.punto,x=(t.irca_max-t.irca_min).clip(lower=0),orientation='h',
                       name='Margen por inconclusos',marker_color=AMBAR))
    f.update_layout(barmode='stack',height=max(350,24*len(t)+120))
    f.update_yaxes(autorange='reversed')
    _plot(f,'calidad_irca','IRCA (%)',max(350,24*len(t)+120))
    st.caption('IRCA estimado sobre muestras de **agua cruda**, con cobertura analítica distinta '
               'según laboratorio. El tramo claro indica el máximo posible bajo resultados inconclusos; '
               'no equivale automáticamente a incumplimiento de agua distribuida.')
    niveles=q.nivel.fillna('Sin categoría').value_counts().reset_index()
    niveles.columns=['Categoría','Muestras']
    st.markdown('#### Distribución de clases IRCA')
    f=go.Figure(go.Bar(x=niveles['Categoría'],y=niveles.Muestras,marker_color=AZUL))
    _plot(f,'clases_irca','Número de muestras',310)
    st.markdown('#### Parámetros fisicoquímicos')
    sel=st.selectbox('Variable', [('pH','ph','unidades'),('Conductividad eléctrica','ce','µS/cm'),
                                    ('Nitrato como ion NO₃','no3_mg','mg/L')],
                     format_func=lambda x:x[0],key='leticia_public_var_calidad')
    f=go.Figure(go.Bar(x=q.punto,y=q[sel[1]],marker_color=VERDE))
    _plot(f,'parametro_calidad',sel[0]+' ('+sel[2]+')',335)
    st.caption('Resultados bajo límite de detección requieren interpretación de censura; '
               'las concentraciones numéricas que representan límites no prueban presencia a ese valor.')
    s=coordenadas_piper(q)
    if len(s)>=3:
        st.markdown('#### Diagrama de Piper · muestras con iones completos')
        h=np.sqrt(3)/2
        f=go.Figure()
        contornos=[[(0,0),(0.5,h),(1,0),(0,0)],
                   [(2,0),(2.5,h),(3,0),(2,0)],
                   [(1.5,0.89),(2.05,1.30),(1.5,1.71),(0.95,1.30),(1.5,0.89)]]
        for sec in contornos:
            f.add_trace(go.Scatter(x=[v[0] for v in sec],y=[v[1] for v in sec],
                                   mode='lines',line=dict(color='rgba(120,140,150,.5)',width=1.6),
                                   showlegend=False,hoverinfo='skip'))
        for x,y,nombre,color in [('cat_x','cat_y','Cationes',VERDE),
                                  ('an_x','an_y','Aniones',AZUL),
                                  ('diam_x','diam_y','Facies (rombo)',AMBAR)]:
            f.add_trace(go.Scatter(x=s[x],y=s[y],mode='markers',name=nombre,
                                   text=s.punto,marker=dict(size=7,color=color,opacity=.85),
                                   hovertemplate='%{text}<extra>'+nombre+'</extra>'))
        for x,y,name in [(0,0,'Ca'),(0.5,h,'Mg'),(1,0,'Na+K'),
                         (2,0,'HCO₃'),(2.5,h,'SO₄'),(3,0,'Cl')]:
            f.add_annotation(x=x,y=y,text=name,showarrow=False,yshift=-13 if y==0 else 16,
                             font=dict(size=11))
        f.update_layout(xaxis=dict(range=[-0.17,3.17],visible=False),
                        yaxis=dict(range=[-0.2,1.90],visible=False,scaleanchor='x'),
                        height=500)
        st.plotly_chart(f,width='stretch',key='leticia_public_piper_completo')
        st.caption('Proyección de Piper reconstruida a partir de los **porcentajes iónicos** '
                   'ya calculados en el explorador público. No se inventan Na/K/HCO₃ para '
                   'las muestras LIA que carecen de resultados completos. '
                   'Los puntos solo representan composición relativa.')
        if 'ward' in s:
            fac=s.groupby(['ward','facies']).size().reset_index(name='Muestras')
            with st.expander('Facies y grupos Ward documentados'):
                st.dataframe(fac,width='stretch',hide_index=True)
    with st.expander('Tabla pública de resultados y límites'):
        columnas=[x for x in ['punto','fecha','grupo','nivel','irca_min','irca_max','cobertura',
                              'ph','ce','no3_mg','facies','ward','no_cumple','inconclusos'] if x in q]
        st.dataframe(q[columnas],width='stretch',hide_index=True)
    st.info('Los resultados provienen de SGS (2022) y LIA-UNAL (2026) y ya estaban '
            'publicados de forma depurada en el explorador. No se incluyen números de informe.')


def _mapa_fuentes() -> None:
    st.subheader('Mapa de puntos y estaciones · referencia pública')
    s=_datos('sitios_publicos.csv')
    if not s.empty:
        categorias=sorted(s.tipo.dropna().unique().tolist())
        elegidos=st.multiselect('Grupos a mostrar',categorias,default=categorias,
                                 key='leticia_public_sitios_tipos')
        q=s.loc[s.tipo.isin(elegidos)].copy()
        f=go.Figure()
        contexto=DATOS_PUBLICOS/'mapa_contexto_publico.json'
        if contexto.is_file():
            try:
                geo=json.loads(contexto.read_text('utf-8'))
                for linea in geo.get('rio_lineas',[]):
                    if len(linea)>=2:
                        f.add_trace(go.Scatter(x=[p[0] for p in linea],y=[p[1] for p in linea],
                           mode='lines',name='Río Amazonas',showlegend=False,
                           line=dict(color='rgba(70,137,190,.5)',width=2.5),hoverinfo='skip'))
                for item in geo.get('limites',[]):
                    for linea in item.get('lineas',[]):
                        if len(linea)>=2:
                            f.add_trace(go.Scatter(x=[p[0] for p in linea],y=[p[1] for p in linea],
                               mode='lines',showlegend=False,line=dict(color='rgba(130,130,130,.4)',
                               dash='dot',width=1),hoverinfo='skip'))
            except (OSError,ValueError,TypeError,KeyError):
                st.caption('El contexto hidrográfico no se pudo dibujar. Los puntos siguen disponibles.')
        for nombre,x in q.groupby('tipo'):
            f.add_trace(go.Scatter(x=x.lon_publica,y=x.lat_publica,mode='markers',name=str(nombre),
               text=x.nombre,marker=dict(size=8,opacity=.78),
               hovertemplate='%{text}<br>Ubicación pública aproximada<extra></extra>'))
        f.update_layout(xaxis=dict(title='Longitud (°)',showgrid=True),
                        yaxis=dict(title='Latitud (°)',scaleanchor='x',scaleratio=1),
                        height=480,legend=dict(orientation='h',y=-0.20))
        st.plotly_chart(f,width='stretch',key='leticia_public_mapa')
        st.caption('Referencias del río y límites tomadas de la versión pública del explorador. No es cartografía topográfica. '
                   'Puntos sensibles redondeados a 0,01° en el explorador público; '
                   'las estaciones oficiales conservan sus coordenadas de catálogo. '
                   'No usar para localizar captaciones particulares.')
    st.markdown('#### Fuentes y criterios')
    st.markdown('''**Fuentes originales:**
    - GRACE/GRACE-FO JPL Mascon RL06.3Mv04 y GLDAS Noah 2.1: anomalías regionales de almacenamiento.
    - IDEAM 48015050: precipitación observada, con correcciones horarias y banderas del taller.
    - IDEAM 48017010 y ANA 10100000 Tabatinga: niveles fluviales con ceros hidrométricos diferentes.
    - CHIRPS v3, IMERG V07 y ERA5: precipitación estimada por píxel; ventanas diarias no siempre idénticas.
    - Transductores Keller y lecturas manuales del proyecto acuífero Leticia–Tabatinga.
    - Calidad del agua: análisis SGS 2022 y LIA-UNAL 2026, ya depurados para versión pública.

    **Metodología:** no se interpolan vacíos de datos; los indicadores de bombeo son reglas
    exploratorias y no actas de operación; las correlaciones no prueban causalidad;
    los niveles de pozo, de río y GWSa no comparten referencia altimétrica.''')
    st.markdown('#### Descargas públicas de datos')
    opciones={
      'Niveles públicos diarios de transductores':'transductores_diarios_publicos.csv',
      'Lecturas manuales públicas':'pozo_unal_manual.csv',
      'IDEAM precipitación diaria con QC':'lluvia_ideam_diaria.csv',
      'Precipitación satelital diaria':'lluvia_satelital_diaria.csv',
      'Nivel IDEAM diario':'rio_diario.csv',
      'Nivel ANA diario':'ana_diario.csv',
      'GRACE público mensual':'grace.csv',
      'Calidad del agua sin informes':'calidad_muestras_publicas.csv',
      'Sitios con coordenadas públicas':'sitios_publicos.csv',
    }
    recurso=st.selectbox('Conjunto de datos público',list(opciones),
                          key='leticia_public_descargas_elige')
    ruta=DATOS_PUBLICOS/opciones[recurso]
    if ruta.is_file():
        st.download_button('Descargar CSV público',ruta.read_bytes(),
                           file_name=opciones[recurso],mime='text/csv',
                           key='leticia_public_descarga_dataset')
    st.caption('Los archivos provienen exclusivamente del HTML de distribución **pública** '
               'entregado para el taller. No se incluyen datos de la versión offline '
               'que puedan tener más identificadores o precisión espacial.')


def mostrar_grace_explorador_publico() -> None:
    """Interfaz con un submenú claro, conectada a los módulos existentes de SIAMS."""
    _portada()
    opciones=['Panorama','Niveles y bombeo','GRACE y río','Validación de lluvia',
              'Calidad del agua','Mapa, fuentes y descargas']
    # Solo con consentimiento y archivo local se habilita la inspección fina.
    if os.environ.get('SIAMS_MONITOREO_INTERNO', '').strip() == '1':
        opciones.append('Revisión instrumental interna')
    pagina=st.selectbox('¿Qué quieres analizar?',opciones,
                        key='siams_grace_navegacion_publica')
    _aviso()
    secciones={
       'Panorama':_panorama,
       'Niveles y bombeo':_niveles,
       'GRACE y río':_grace_rio,
       'Validación de lluvia':_lluvia,
       'Calidad del agua':_calidad,
       'Mapa, fuentes y descargas':_mapa_fuentes,
    }
    if pagina == 'Revisión instrumental interna':
        _interno()
    else:
        secciones[pagina]()


# Procesamiento instrumental solo local: la vista pública anterior funciona sin esto.
PRIVADO_CSV = RAIZ / 'privado/monitoreo_leticia/numae_columna_lluvia_diaria_2026.csv'
NIVELES_CSV = RAIZ / 'data/processed/niveles/niveles_leticia.csv'
POZOS_CSV = RAIZ / 'data/processed/niveles/pozos.csv'

@st.cache_data(show_spinner=False)
def _datos_numae_privados(mtime: int) -> pd.DataFrame:
    return preparar_numae_diario(leer_csv_seguro(
        PRIVADO_CSV, {'fecha','columna_madrugada_m','fraccion_horas_bombeo','fraccion_horas_seco'}
    ))

@st.cache_data(show_spinner=False)
def _datos_profesora(mtime: int) -> pd.DataFrame:
    return leer_csv_seguro(NIVELES_CSV, {'fecha','pozo_id','calidad'})

def _estilo_grafico(fig, eje_y: str = '', altura: int = 390):
    return _grafico(fig, eje_y, altura)

def _tarjeta(texto: str, valor: str, detalle: str, color: str = VERDE):
    with st.container(border=True):
        st.caption(texto)
        st.metric(texto, valor)
        st.caption(detalle)


def _interno():
    st.divider()
    st.markdown('#### Monitoreo instrumental · revisión interna')
    st.warning('**Uso interno SIAMS.** Se muestran registros procesados que pueden estar sujetos a '
               'acuerdos de acceso. No compartir capturas ni publicar estas series sin autorización.')
    tabs = st.tabs(['Numae: lluvia y nivel', 'Bombeo y calidad', 'Criterios y referencias'])
    diario = pd.DataFrame()
    if PRIVADO_CSV.is_file():
        try:
            diario = _datos_numae_privados(PRIVADO_CSV.stat().st_mtime_ns)
        except (ValueError, OSError, pd.errors.ParserError) as exc:
            st.error(f'No se pudo interpretar el CSV interno de Numae: {exc}')
    with tabs[0]:
        if diario.empty:
            st.info('Para el análisis diario, copia el CSV interno del explorador en `privado/monitoreo_leticia/`. '
                    'El script incluido lo prepara directamente desde el ZIP; no debes agregarlo a Git.')
        else:
            fuentes = [f for f, c in FUENTES_DIARIAS.items() if diario[c].notna().sum() > 5]
            fuente = st.selectbox('Precipitación diaria', fuentes, key='siamsobs_lluvia_interna')
            lluvia = FUENTES_DIARIAS[fuente]
            c1, c2, c3, c4 = st.columns(4)
            with c1:
                _tarjeta('Días con columna', str(int(diario.columna_madrugada_m.notna().sum())),
                         'Columna de madrugada · m')
            with c2:
                _tarjeta('Días con lluvia', str(int(diario[lluvia].notna().sum())),
                         fuente, AZUL)
            with c3:
                _tarjeta('Mediana de columna', f'{diario.columna_madrugada_m.median():.2f} m',
                         'No equivale a profundidad del nivel', AMBAR)
            with c4:
                _tarjeta('Mayor día de lluvia', f'{diario[lluvia].max():.1f} mm',
                         'Solo dentro del período de la sonda', MORADO)
            graf = go.Figure()
            graf.add_trace(go.Bar(x=diario.fecha, y=diario[lluvia], name=f'{fuente} · lluvia (mm)',
                                  marker_color='rgba(55,104,154,.55)'))
            graf.add_trace(go.Scatter(x=diario.fecha, y=diario.columna_madrugada_m,
                                      line=dict(color=VERDE, width=3), name='Numae · columna de madrugada (m)',
                                      yaxis='y2', connectgaps=False))
            graf.update_layout(yaxis=dict(title='Precipitación (mm/día)'),
                               yaxis2=dict(title='Columna sobre sensor (m)', overlaying='y', side='right'))
            st.plotly_chart(_estilo_grafico(graf, 'Precipitación diaria (mm)', 470),
                            width='stretch', key='siamsobs_rain_well')
            st.caption('Columna de madrugada según el procesamiento del explorador; las observaciones sin dato '
                       'no se completan ni interpolan. No se presenta como cota absoluta.')
            lag = correlacion_lluvia_cambio(diario, lluvia)
            fig = go.Figure(go.Bar(x=lag['Desfase (días)'], y=lag['r Pearson'],
                                   text=lag['Pares válidos'], textposition='outside',
                                   marker_color=VERDE))
            fig.add_hline(y=0, line_color='rgba(100,100,100,.35)')
            st.plotly_chart(_estilo_grafico(fig, 'r entre lluvia y cambio diario de columna', 355),
                            width='stretch', key='siamsobs_lag_dia')
            valid = lag.dropna(subset=['r Pearson'])
            if not valid.empty:
                mejor = valid.iloc[valid['r Pearson'].abs().argmax()]
                st.info(f"La asociación absoluta más alta se observa con **{int(mejor['Desfase (días)'])} "
                        f"día(s)** de desfase (r = **{mejor['r Pearson']:+.2f}**, "
                        f"n = **{int(mejor['Pares válidos'])}**). Es una correlación exploratoria; "
                        'no prueba recarga puntual ni causalidad.')
            st.caption('Para el análisis de desfases se usa Δcolumna entre días consecutivos, '
                       'no la columna sin diferenciar; días sin registro permanecen vacíos.')
    with tabs[1]:
        if not diario.empty:
            mensual_expl = diario[['fecha', 'fraccion_horas_bombeo',
                                   'fraccion_horas_seco']].copy()
            mensual_expl['mes'] = mensual_expl['fecha'].dt.to_period('M').dt.to_timestamp()
            mensual_expl = mensual_expl.groupby('mes')[['fraccion_horas_bombeo',
                'fraccion_horas_seco']].mean().mul(100).reset_index()
            b = go.Figure()
            b.add_trace(go.Scatter(x=mensual_expl.mes,
                y=mensual_expl.fraccion_horas_bombeo, name='Posible bombeo',
                mode='lines+markers', line=dict(color=AMBAR, width=3)))
            b.add_trace(go.Scatter(x=mensual_expl.mes,
                y=mensual_expl.fraccion_horas_seco, name='Sensor posiblemente fuera del agua',
                mode='lines+markers', line=dict(color=MORADO, width=3)))
            st.markdown('**Lectura mensual del explorador: bombeo y sensor al aire**')
            st.plotly_chart(_estilo_grafico(b, 'Fracción media diaria de horas (%)', 350),
                            width='stretch', key='siamsobs_eventos_numae')
            st.caption('Bombeo: caída de más de 0,5 m respecto a la mediana nocturna '
                       'del mismo día. Sensor al aire: columna inferior a 0,8 m. '
                       'Son umbrales exploratorios del explorador; no constituyen '
                       'un registro operativo verificado de la bomba.')
        if not NIVELES_CSV.is_file():
            st.info('Sin datos procesados en `data/processed/niveles/niveles_leticia.csv`.')
        else:
            try:
                niveles = _datos_profesora(NIVELES_CSV.stat().st_mtime_ns)
                mensual, horaria = calidad_horaria(niveles)
            except (ValueError, OSError, pd.errors.ParserError) as exc:
                st.error(f'No se pudieron procesar las banderas: {exc}')
                mensual, horaria = pd.DataFrame(), pd.DataFrame()
            if not mensual.empty:
                c1, c2, c3 = st.columns(3)
                with c1:
                    _tarjeta('Registros Numae', str(int(mensual.registros.sum())),
                             'Archivo procesado por el semillero')
                with c2:
                    _tarjeta('Con bandera', f'{mensual.marcados.sum() / mensual.registros.sum():.1%}',
                             'Posible bombeo o sensor fuera del agua', AMBAR)
                with c3:
                    _tarjeta('Meses observados', str(len(mensual)),
                             'Sin inventar horarios faltantes', AZUL)
                f1 = go.Figure(go.Bar(x=mensual.mes, y=mensual.fraccion_marcados_pct,
                                      marker_color=AMBAR, name='Registros marcados'))
                st.plotly_chart(_estilo_grafico(f1, 'Porcentaje de registros marcados (%)', 350),
                                width='stretch', key='siamsobs_flags_mes')
                f2 = go.Figure(go.Bar(x=horaria.hora, y=horaria.fraccion_marcados_pct,
                                      marker_color=AZUL, name='Registros marcados'))
                f2.update_xaxes(dtick=1, title='Hora del día · hora del archivo procesado')
                st.plotly_chart(_estilo_grafico(f2, 'Porcentaje de registros marcados (%)', 350),
                                width='stretch', key='siamsobs_flags_hora')
                st.caption('Las banderas de la profesora son criterios automáticos de posible bombeo o sensor '
                           'fuera del agua, NO un registro confirmado de encendido y apagado de una bomba. '
                           'El denominador usa los registros efectivamente disponibles.')
                with st.expander('Tabla de calidad mensual'):
                    st.dataframe(mensual, width='stretch', hide_index=True)
    with tabs[2]:
        st.markdown('''**Interpretación del sensor Numae**

- El explorador documenta que una instalación inicial de **7 m** no es compatible con columnas medidas
  de hasta aproximadamente **8,10 m**. No determina por sí solo la profundidad real.
- La actualización del semillero en `config/pozos_monitoreo.csv` utiliza **17 m** (noviembre de 2026),
  aún sujeto a verificación de instalación y referencia vertical.
- El panel **no recalcula ni publica cotas absolutas** de Numae. Presenta columna sobre el sensor,
  lluvia, cambios relativos y banderas de calidad.
- Una medición manual simultánea sin bombeo y la referencia exacta del brocal/cable permitirían
  validar la conversión futura a profundidad y cota.

**Uso de datos:** la serie lluvia–Numae del explorador se identifica como material interno. Su
CSV debe permanecer en la carpeta privada ignorada por Git. No se exporta desde este panel.''')
        if POZOS_CSV.is_file():
            meta = pd.read_csv(POZOS_CSV)
            meta = meta.loc[meta.pozo_id.eq('LET-NUMAE')]
            if not meta.empty:
                d = meta.iloc[0]
                st.caption('Configuración del semillero (nov-2026): '
                           f"profundidad asumida = {d.prof_sensor_m:g} m bajo terreno; "
                           f"cota DEM aproximada = {d.cota_terreno_msnm:.2f} m s. n. m. "
                           'La cota DEM no es levantamiento topográfico.')


def mostrar_panel_integrado_leticia() -> None:
    """Punto de entrada estable utilizado por grace_leticia.py."""
    mostrar_grace_explorador_publico()


__all__ = ['mostrar_panel_integrado_leticia', 'mostrar_grace_explorador_publico']
