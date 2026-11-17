"""Vista independiente del río Amazonas, con los CSV públicos que utiliza GRACE."""
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from .ana_leticia_datos import cargar_series, resumen, mensual, comparar, PERIODOS, periodo_consulta
from .ideam_leticia import _css, _metrica
from .grace_interfaz import _grafico

MESES = ['Ene','Feb','Mar','Abr','May','Jun','Jul','Ago','Sep','Oct','Nov','Dic']
COLORES = {'ANA Tabatinga':'#18796F', 'IDEAM Leticia':'#4284B3'}


def _plot(fig, eje, key):
    st.plotly_chart(_grafico(fig, eje), width='stretch', key='ana_leticia_'+key)


def _descarga(df, etiqueta, nombre):
    st.download_button(etiqueta, df.to_csv().encode('utf-8-sig'), nombre, 'text/csv', key=nombre)


def mostrar_ana_leticia():
    _css()
    st.markdown('''<div class="siams-ideam-hero"><div class="eyebrow">SIAMS / Territorio / Leticia</div><h1>Río Amazonas · <span>ANA / IDEAM</span></h1><p>Monitoreo histórico del nivel del río entre Tabatinga (Brasil) y Leticia (Colombia).</p><div class="ideam-chip">ANA / IDEAM · Explorador Leticia, versión pública</div></div>''', unsafe_allow_html=True)
    series, origen, avisos = cargar_series()
    for n, a in avisos.items():
        st.warning(f'{n}: {a}')
    if not series:
        st.info('No se encontraron los CSV públicos existentes. Comprueba data/processed/observatorio_leticia/ y su subcarpeta explorador_publico/.')
        return
    # Estilos locales: no cambian las tarjetas de IDEAM ni el resto de SIAMS.
    st.markdown("""<style>
    .st-key-ana_resumen .siams-ideam-metric {
        min-height: 98px; padding: 12px 15px; margin-bottom: 0;
        background: var(--background-color, #fff);
        box-shadow: none; border-radius: 11px; border-left-width: 3px;
    }
    .st-key-ana_resumen .siams-ideam-metric .m-label {font-size: .79rem;}
    .st-key-ana_resumen .siams-ideam-metric .m-val {font-size: clamp(1.2rem, 1.9vw, 1.75rem);}
    .st-key-ana_resumen .siams-ideam-metric .m-note {margin-top: 5px;}
    .st-key-ana_filtros [data-testid="stRadio"] div[role="radiogroup"] {gap: .55rem; flex-wrap: wrap;}
    .st-key-ana_filtros [data-testid="stRadio"] div[role="radiogroup"] > label {
        border: 1px solid rgba(31,127,108,.28); border-radius: 8px; padding: 6px 10px; margin: 0;
    }
    </style>""", unsafe_allow_html=True)
    with st.container(border=True, key='ana_filtros'):
        st.markdown('**Explora el nivel del río**')
        a, b = st.columns([1, 2])
        with a:
            nombre = st.selectbox('Estación hidrométrica', list(series), key='ana_leticia_estacion')
            s = series[nombre]
            primero, ultimo = periodo_consulta(s)
            n_total = int(s.notna().sum())
            st.caption(f'Disponibilidad: {primero:%d/%m/%Y} – {ultimo:%d/%m/%Y} · {n_total:,} días observados'.replace(',', '.'))
        with b:
            modo = st.radio('Periodo de consulta', PERIODOS, horizontal=True,
                            key='ana_leticia_modo_'+nombre, index=0)
            if modo == 'Personalizado':
                # Claves independientes por estación y límites de datos.
                sufijo = f'{nombre}_{primero:%Y%m%d}_{ultimo:%Y%m%d}'
                c1, c2 = st.columns(2)
                if primero == ultimo:
                    desde = hasta = primero.date()
                    st.caption('Solo existe una fecha disponible para seleccionar.')
                else:
                    desde = c1.date_input('Desde', value=primero.date(), min_value=primero.date(),
                                          max_value=ultimo.date(), key='ana_inicio_'+sufijo, format='DD/MM/YYYY')
                    hasta = c2.date_input('Hasta', value=ultimo.date(), min_value=primero.date(),
                                          max_value=ultimo.date(), key='ana_fin_'+sufijo, format='DD/MM/YYYY')
                try:
                    ini, fin = periodo_consulta(s, modo, desde, hasta)
                except ValueError as exc:
                    st.warning(str(exc))
                    return
            else:
                ini, fin = periodo_consulta(s, modo)
            st.caption(f'Periodo aplicado: {ini:%d/%m/%Y} – {fin:%d/%m/%Y}. Los accesos rápidos terminan en la última fecha observada, no en la fecha de hoy.')
    d = s.loc[ini:fin]
    v = d.dropna()
    m = resumen(d)
    if n_total == 1:
        st.warning('El archivo cargado para esta estación contiene una sola observación válida. Cambiar el periodo no generará más datos históricos.')
    elif not len(v):
        st.info('No hay observaciones válidas en el periodo elegido. Selecciona otro intervalo.')
    with st.container(key='ana_resumen'):
        cols = st.columns(4)
        with cols[0]: _metrica('Días observados', f"{m['dias']:,}".replace(',', '.'), f'De {(fin-ini).days+1:,} días del periodo'.replace(',', '.'))
        with cols[1]: _metrica('Cobertura diaria', f"{m['cobertura']:.1f}%", 'Sin rellenar vacíos')
        with cols[2]: _metrica('Último nivel observado', f'{v.iloc[-1]:.2f} m' if len(v) else '—', f'{v.index[-1]:%d/%m/%Y}' if len(v) else 'Sin observaciones', teal=True)
        with cols[3]: _metrica('Amplitud observada', f'{v.max()-v.min():.2f} m' if len(v) >= 2 else '—', 'Máximo − mínimo' if len(v) >= 2 else 'Se requieren 2 observaciones')
    st.caption(f'Fuente: {origen[nombre]} · Nivel en metros respecto al cero hidrométrico local; no es elevación geodésica ni caudal.')
    f=go.Figure(go.Scatter(x=d.index,y=d,mode='lines+markers' if len(v)<=30 else 'lines',name=nombre,line=dict(color=COLORES[nombre]),marker=dict(size=6),connectgaps=False))
    with st.container(border=True):
        st.subheader('Historia del nivel del río')
        _plot(f,'Nivel (m) · referencia local','historia')
    mm=mensual(d)
    if not mm.empty and mm.nivel_m.notna().any():
        left,right=st.columns(2)
        with left:
            with st.container(border=True):
                st.subheader('Ciclo estacional del nivel')
                clim=mm.nivel_m.groupby(mm.index.month).agg(['mean','count']).reindex(range(1,13))
                f=go.Figure(go.Scatter(x=MESES,y=clim['mean'],customdata=clim['count'].fillna(0),mode='lines+markers',line=dict(color=COLORES[nombre]),connectgaps=False,hovertemplate='%{x}: %{y:.2f} m<br>Meses completos: %{customdata}<extra></extra>'))
                _plot(f,'Media mensual (m)','ciclo')
                st.caption('Promedio de meses completos por mes calendario; no es una normal oficial.')
        with right:
            with st.container(border=True):
                st.subheader('Calendario histórico de niveles')
                matrix=mm.nivel_m.to_frame('nivel').assign(anio=mm.index.year,mes=mm.index.month).pivot(index='anio',columns='mes',values='nivel').reindex(columns=range(1,13))
                f=go.Figure(go.Heatmap(x=MESES,y=matrix.index,z=matrix.to_numpy(),colorscale='Teal',colorbar=dict(title='m'),hoverongaps=False))
                _plot(f,'Año','calendario')
                st.caption('Cada celda es la media de un mes completo. Vacíos: sin datos suficientes.')
    else:
        st.info('No hay meses completos en este periodo para calcular el ciclo estacional o el calendario histórico.')
    st.subheader('Comparación ANA Tabatinga e IDEAM Leticia')
    st.caption('Se usa el periodo seleccionado y únicamente fechas comunes. Se resta a cada estación su propia media de ese periodo común, como en GRACE; no se equiparan sus ceros hidrométricos.')
    rel, stats = comparar({n:x.loc[ini:fin] for n,x in series.items()})
    a,b=st.columns(2)
    a.metric('Días comunes', stats['n'])
    b.metric('Correlación Pearson', f"{stats['r_pearson']:.3f}" if pd.notna(stats['r_pearson']) else '—')
    if stats['n']>=30:
        f=go.Figure()
        for n in rel:
            f.add_trace(go.Scatter(x=rel.index,y=rel[n],name=n,mode='lines',connectgaps=False,line=dict(color=COLORES[n])))
        _plot(f,'Nivel relativo a la media común (m)','comparacion')
        _descarga(rel,'Descargar niveles relativos (fechas comunes)','SIAMS_ANA_IDEAM_relativos.csv')
        st.caption('Una correlación alta describe variaciones simultáneas; no demuestra igualdad de niveles, caudal o causalidad.')
    else:
        st.info('Se requieren al menos 30 días comunes para el contraste relativo, siguiendo el criterio del módulo GRACE.')
    with st.expander('Disponibilidad, fuentes, metodología y descargas'):
        st.dataframe(pd.DataFrame([{'Estación':n,'Archivo':origen[n],**resumen(x)} for n,x in series.items()]),hide_index=True,width='stretch')
        st.write('Fuentes: ANA Brasil e IDEAM Colombia; archivos públicos del Explorador Leticia del proyecto SIAMS. Se conservan los registros originales; no se interpolan datos ni se calculan caudales sin curva de gasto. Las medias mensuales requieren todos los días del calendario. No hay actualización de ANA en tiempo real en esta versión.')
        _descarga(d.to_frame(),'Descargar nivel diario del periodo','SIAMS_nivel_rio_diario.csv')
        _descarga(mm,'Descargar nivel mensual y cobertura','SIAMS_nivel_rio_mensual.csv')
