# Archivo reorganizado a partir de SIAMS V39.
# No modificar la lógica científica aquí sin pruebas y revisión metodológica.
from __future__ import annotations

from pathlib import Path
from textwrap import dedent
from html import escape
import math
import unicodedata
import base64
import subprocess
import tempfile
import re

import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

try:
    import numpy as np
    import xarray as xr
except ImportError:
    np = None
    xr = None



MESES = [
    "Ene", "Feb", "Mar", "Abr", "May", "Jun",
    "Jul", "Ago", "Sep", "Oct", "Nov", "Dic",
]

UNAL_SEDES = pd.DataFrame([
    {
        "Sede": "Bogotá",
        "Ciudad": "Bogotá D.C.",
        "lat": 4.6386,
        "lon": -74.0841,
        "Estado": "Territorio integrado en SIAMS",
        "Descripcion": "Sede Bogotá, incorporada al prototipo con un piloto cartográfico de ubicación por niveles.",
        "Tamano": 16,
    },
    {
        "Sede": "Medellín",
        "Ciudad": "Medellín, Antioquia",
        "lat": 6.260650,
        "lon": -75.579592,
        "Estado": "Territorio integrado en SIAMS",
        "Descripcion": "Sede Medellín, incorporada al prototipo con cartografía y climatología.",
        "Tamano": 16,
    },
    {
        "Sede": "Manizales",
        "Ciudad": "Manizales, Caldas",
        "lat": 5.070353,
        "lon": -75.513816,
        "Estado": "Otra sede UNAL (contexto)",
        "Descripcion": "Sede Manizales de la Universidad Nacional de Colombia.",
        "Tamano": 11,
    },
    {
        "Sede": "Palmira",
        "Ciudad": "Palmira, Valle del Cauca",
        "lat": 3.512231,
        "lon": -76.307211,
        "Estado": "Otra sede UNAL (contexto)",
        "Descripcion": "Sede Palmira de la Universidad Nacional de Colombia.",
        "Tamano": 11,
    },
    {
        "Sede": "Amazonia",
        "Ciudad": "Leticia, Amazonas",
        "lat": -4.193717,
        "lon": -69.941001,
        "Estado": "Territorio integrado en SIAMS",
        "Descripcion": "Sede Amazonia, trabajada en SIAMS como territorio Leticia.",
        "Tamano": 16,
    },
    {
        "Sede": "Caribe",
        "Ciudad": "San Andrés Isla",
        "lat": 12.536552,
        "lon": -81.707935,
        "Estado": "Territorio integrado en SIAMS",
        "Descripcion": "Sede Caribe, representada en SIAMS con información de San Andrés.",
        "Tamano": 16,
    },
    {
        "Sede": "Orinoquía",
        "Ciudad": "Arauca, Arauca",
        "lat": 7.012222763876252,
        "lon": -70.74338825990411,
        "Estado": "Territorio integrado en SIAMS",
        "Descripcion": "Sede Orinoquía, incorporada al prototipo como territorio Arauca.",
        "Tamano": 16,
    },
    {
        "Sede": "Tumaco",
        "Ciudad": "Tumaco, Nariño",
        "lat": 1.610206,
        "lon": -78.720520,
        "Estado": "Territorio integrado en SIAMS",
        "Descripcion": "Sede Tumaco, trabajada en SIAMS con cartografía y datos hidroclimáticos.",
        "Tamano": 16,
    },
    {
        "Sede": "La Paz",
        "Ciudad": "La Paz, Cesar",
        "lat": 10.390218033322455,
        "lon": -73.20038917337925,
        "Estado": "Territorio integrado en SIAMS",
        "Descripcion": "Sede de La Paz, incorporada al prototipo SIAMS.",
        "Tamano": 16,
    },
])

TERRITORIOS = {
    "Bogotá": {
        "region": "Región Andina",
        "departamento": "Bogotá D.C.",
        "sede": "Universidad Nacional de Colombia – Sede Bogotá",
        "lat": 4.6386,
        "lon": -74.0841,
        "area_principal": "Campus Ciudad Universitaria",
        "contexto": "Bogotá D.C. y entorno metropolitano",
        "fuente_clima": "Pendiente de integración",
        "estado_datos": "Piloto cartográfico de ubicación habilitado",
        "descripcion": (
            "La Sede Bogotá se incorpora al prototipo SIAMS mediante un módulo de ubicación "
            "multiescala que permite pasar de Colombia a Bogotá, luego al campus y finalmente "
            "a una vista web interactiva de la Ciudad Universitaria."
        ),
        "precipitacion": [],
        "temperatura": [],
        "humedad": [],
        "hallazgo": (
            "La ubicación de la sede se presenta como una secuencia cartográfica de tres escalas "
            "complementada con un mapa interactivo para navegación, zoom y consulta espacial."
        ),
    },
    "Leticia": {
        "region": "Amazonía colombiana",
        "departamento": "Amazonas",
        "sede": "Universidad Nacional de Colombia – Sede Amazonia",
        "lat": -4.193717,
        "lon": -69.941001,
        "area_principal": "15 km",
        "contexto": "Municipio de Leticia",
        "fuente_clima": "NASA POWER",
        "estado_datos": "IDEAM con disponibilidad limitada",
        "descripcion": (
            "Leticia se ubica en el extremo sur de Colombia, junto al río Amazonas. "
            "El territorio presenta alta humedad, abundante precipitación y una fuerte "
            "relación entre los ecosistemas amazónicos, los sistemas fluviales y las "
            "dinámicas urbanas transfronterizas."
        ),
        "precipitacion": [260, 275, 320, 335, 310, 245, 190, 175, 205, 250, 280, 300],
        "temperatura": [26.0, 26.1, 25.8, 25.6, 25.5, 25.2, 25.0, 25.4, 26.0, 26.3, 26.2, 26.1],
        "humedad": [86, 86, 88, 89, 89, 88, 86, 84, 84, 85, 86, 86],
        "hallazgo": (
            "La disponibilidad de series IDEAM continuas es limitada, por lo que "
            "NASA POWER se plantea como fuente climática principal para el prototipo."
        ),
    },
    "Tumaco": {
        "region": "Pacífico colombiano",
        "departamento": "Nariño",
        "sede": "Universidad Nacional de Colombia – Sede Tumaco",
        "lat": 1.610206,
        "lon": -78.720520,
        "area_principal": "25 km",
        "contexto": "Hasta 50 km",
        "fuente_clima": "IDEAM + NASA POWER",
        "estado_datos": "Series parciales complementadas",
        "descripcion": (
            "Tumaco se localiza en la costa pacífica colombiana. El territorio se "
            "caracteriza por elevada precipitación, alta humedad y una interacción "
            "permanente entre sistemas continentales, costeros, estuarinos y marinos."
        ),
        "precipitacion": [310, 285, 330, 390, 430, 360, 280, 240, 265, 315, 345, 330],
        "temperatura": [26.2, 26.4, 26.3, 26.1, 25.9, 25.7, 25.6, 25.7, 25.8, 26.0, 26.1, 26.2],
        "humedad": [84, 84, 85, 86, 87, 86, 85, 84, 84, 85, 85, 84],
        "hallazgo": (
            "En Tumaco existen algunas series IDEAM útiles, aunque su continuidad "
            "debe evaluarse y complementarse con NASA POWER."
        ),
    },
    "Medellín": {
        "region": "Región Andina",
        "departamento": "Antioquia",
        "sede": "Universidad Nacional de Colombia – Sede Medellín",
        "lat": 6.262190,
        "lon": -75.576968,
        "area_principal": "Entorno urbano y regional",
        "contexto": "Valle de Aburrá",
        "fuente_clima": "NASA POWER",
        "estado_datos": "Climatología NASA POWER incorporada",
        "descripcion": (
            "La Sede Medellín se localiza en el Valle de Aburrá, un territorio urbano-andino "
            "con fuertes contrastes topográficos, una red de quebradas tributarias del río Medellín "
            "y condicionantes geológicos, ecológicos y de amenaza por inundación."
        ),
        "precipitacion": [], "temperatura": [], "humedad": [],
        "hallazgo": (
            "Para esta versión se prioriza la integración cartográfica: geología regional, "
            "estructura ecológica principal y amenaza por inundación."
        ),
    },
    "San Andrés": {
        "region": "Caribe insular colombiano",
        "departamento": "San Andrés, Providencia y Santa Catalina",
        "sede": "Universidad Nacional de Colombia – Sede Caribe",
        "lat": 12.536552,
        "lon": -81.707935,
        "area_principal": "Isla de San Andrés",
        "contexto": "Territorio insular y acuífero",
        "fuente_clima": "NASA POWER",
        "estado_datos": "Climatología NASA POWER + cartografía hidrogeológica",
        "descripcion": (
            "San Andrés es un territorio insular del Caribe colombiano donde la disponibilidad "
            "de agua dulce depende estrechamente de la lluvia y de los acuíferos de la isla. "
            "La vulnerabilidad del acuífero y la calidad de las aguas subterráneas son componentes "
            "centrales para la lectura hidroambiental del territorio."
        ),
        "precipitacion": [], "temperatura": [], "humedad": [],
        "hallazgo": (
            "La cartografía de CORALINA permite integrar geología, vulnerabilidad del acuífero, "
            "nitratos y microcuencas/arroyos estacionales en una misma lectura territorial."
        ),
    },
    "Arauca": {
        "region": "Orinoquía colombiana",
        "departamento": "Arauca",
        "sede": "Universidad Nacional de Colombia – Sede Orinoquía",
        "lat": 7.012222763876252,
        "lon": -70.74338825990411,
        "area_principal": "Entorno de la Sede Orinoquía",
        "contexto": "Municipio de Arauca y llanura aluvial",
        "fuente_clima": "IDEAM + NASA POWER",
        "estado_datos": "IDEAM procesado + NASA POWER; ambas fuentes se comparan sin fusionar series",
        "descripcion": (
            "Arauca se localiza en la Orinoquía colombiana, en un territorio de llanura con "
            "fuerte influencia de los sistemas fluviales y marcada estacionalidad hidroclimática. "
            "La Sede Orinoquía se incorpora al prototipo para ampliar la comparación entre regiones."
        ),
        "precipitacion": [], "temperatura": [], "humedad": [],
        "hallazgo": (
            "IDEAM se utiliza como referencia terrestre para precipitación y temperatura; "
            "NASA POWER se conserva para comparación y para viento, presión y radiación."
        ),
    },
    "La Paz": {
        "region": "Caribe continental",
        "departamento": "Cesar",
        "sede": "Universidad Nacional de Colombia – Sede de La Paz",
        "lat": 10.390218033322455,
        "lon": -73.20038917337925,
        "area_principal": "Entorno de la Sede de La Paz",
        "contexto": "Municipio de La Paz y valle del Cesar",
        "fuente_clima": "NASA POWER",
        "estado_datos": "Módulo territorial habilitado; clima se activa al detectar el Excel procesado",
        "descripcion": (
            "La Paz se localiza en el departamento del Cesar, en el Caribe continental colombiano. "
            "Su incorporación permite ampliar el análisis hidroambiental hacia un territorio con "
            "condiciones climáticas y geológicas distintas a las demás sedes priorizadas."
        ),
        "precipitacion": [], "temperatura": [], "humedad": [],
        "hallazgo": (
            "El territorio queda preparado para integrar clima, cartografía y el análisis regional "
            "de anomalías de almacenamiento de agua subterránea mediante GRACE/GLDAS."
        ),
    },
}

ESTADO_COMPONENTES = {
    "Bogotá": [
        ("Identificación y contexto", "Completo", "Sede, coordenadas y contexto territorial incorporados."),
        ("Cartografía e hidrología", "En proceso", "Piloto de ubicación multiescala incorporado; hidrología temática queda para una fase posterior."),
        ("Clima", "Pendiente", "No se ha integrado todavía una base climática específica para Bogotá."),
        ("Geología", "Pendiente", "No se ha incorporado todavía cartografía geológica específica."),
        ("Cobertura y relieve", "Pendiente", "No se han incorporado aún capas temáticas de cobertura o relieve."),
        ("Estaciones y calidad", "Pendiente", "Inventario de estaciones y control de datos por consolidar."),
        ("Hidrogeología", "Pendiente", "Componente por desarrollar."),
        ("IRCA", "Pendiente", "Componente por desarrollar."),
        ("Hidrogeoquímica", "Pendiente", "Componente por desarrollar."),
        ("Monitoreo", "Sin datos", "No se han incorporado series validadas de monitoreo."),
    ],
    "Leticia": [
        ("Identificación y contexto", "Completo", "Sede, localización y síntesis territorial incorporadas."),
        ("Cartografía e hidrología", "Completo", "Mapas regionales de hidrografía, humedales e inundación."),
        ("Clima", "Completo", "NASA POWER procesado como fuente continua principal."),
        ("Geología", "Completo", "Mapa regional del Trapecio Sur incorporado."),
        ("Cobertura y relieve", "Completo", "Coberturas y geomorfología disponibles como referencia."),
        ("Estaciones y calidad", "En proceso", "IDEAM documentado, pero con continuidad insuficiente para la climatología principal."),
        ("Hidrogeología", "En proceso", "Existe referencia académica de pozos; falta consolidar unidades y atributos."),
        ("IRCA", "En proceso", "Mapa académico disponible; faltan series oficiales consolidadas por periodo."),
        ("Hidrogeoquímica", "Pendiente", "No hay una base completa con coordenadas, unidades e iones mayoritarios."),
        ("Monitoreo", "Sin datos", "No se han incorporado series validadas de sondas o nivel."),
    ],
    "Tumaco": [
        ("Identificación y contexto", "Completo", "Sede, localización y síntesis territorial incorporadas."),
        ("Cartografía e hidrología", "Completo", "Hidrografía, manglares e inundación regional incorporados."),
        ("Clima", "Completo", "IDEAM y NASA POWER integrados sin fusionar las series."),
        ("Geología", "Completo", "Mapa geológico regional del POMCA del río Mira."),
        ("Cobertura y relieve", "Completo", "Coberturas y pendientes del contexto regional."),
        ("Estaciones y calidad", "Completo", "Completitud, periodos, estaciones y decisión por variable documentados."),
        ("Hidrogeología", "En proceso", "Falta consolidar unidades hidrogeológicas y pozos georreferenciados."),
        ("IRCA", "Pendiente", "No se ha localizado una base georreferenciada equivalente a la de Leticia."),
        ("Hidrogeoquímica", "Pendiente", "Faltan muestras completas con ubicación, fecha, unidades e iones."),
        ("Monitoreo", "Sin datos", "No se han incorporado series validadas de sondas o nivel."),
    ],    "Medellín": [
        ("Identificación y contexto", "Completo", "Sede, localización y síntesis territorial incorporadas."),
        ("Cartografía e hidrología", "Completo", "Amenaza por inundación incorporada desde el POT de Medellín."),
        ("Clima", "Completo", "NASA POWER procesado e incorporado como fuente climática continua."),
        ("Geología", "Completo", "Plancha 228 del Servicio Geológico Colombiano incorporada."),
        ("Cobertura y relieve", "En proceso", "Estructura Ecológica Principal incorporada como contexto ambiental."),
        ("Estaciones y calidad", "En proceso", "NASA POWER documentado; estaciones IDEAM locales quedan como ampliación futura."),
        ("Hidrogeología", "Pendiente", "No se ha incorporado aún cartografía hidrogeológica específica."),
        ("IRCA", "Pendiente", "No se ha incorporado una base georreferenciada de calidad del agua."),
        ("Hidrogeoquímica", "Pendiente", "No hay muestras hidrogeoquímicas integradas en esta versión."),
        ("Monitoreo", "Sin datos", "No se han incorporado series validadas de sondas o nivel."),
    ],
    "San Andrés": [
        ("Identificación y contexto", "Completo", "Sede Caribe, localización y contexto insular incorporados."),
        ("Cartografía e hidrología", "Completo", "Microcuencas y arroyos estacionales incorporados desde CORALINA."),
        ("Clima", "Completo", "NASA POWER procesado e incorporado como fuente climática continua."),
        ("Geología", "Completo", "Conformación geológica de la isla incorporada."),
        ("Cobertura y relieve", "Pendiente", "No se incluyó aún una capa específica de cobertura o relieve."),
        ("Estaciones y calidad", "En proceso", "NASA POWER documentado; falta consolidar estaciones terrestres locales por variable."),
        ("Hidrogeología", "Completo", "Vulnerabilidad de las rocas que conforman los acuíferos incorporada."),
        ("IRCA", "Pendiente", "No se ha incorporado aún una serie IRCA georreferenciada."),
        ("Hidrogeoquímica", "En proceso", "Mapa de concentraciones de nitratos incorporado como antecedente."),
        ("Monitoreo", "Sin datos", "No se han incorporado series validadas de sondas o nivel."),
    ],
    "Arauca": [
        ("Identificación y contexto", "Completo", "Sede Orinoquía, coordenadas y síntesis territorial incorporadas."),
        ("Cartografía e hidrología", "En proceso", "Se incorporan mapas IDEAM de oferta hídrica, demanda industrial y vertimientos como contexto regional y nacional."),
        ("Clima", "Completo", "IDEAM procesado y NASA POWER se integran como fuentes separadas y comparables."),
        ("Geología", "En proceso", "Mapa Geológico de Colombia 2023 incorporado como referencia regional; falta cartografía de mayor detalle para el entorno de la sede."),
        ("Cobertura y relieve", "Pendiente", "Faltan capas de cobertura, relieve o pendientes específicas para Arauca."),
        ("Estaciones y calidad", "En proceso", "Queda habilitado el inventario de datos y fuentes."),
        ("Hidrogeología", "En proceso", "Se incorporan el sistema acuífero Arauca-Arauquita, PEXAS y mapas IDEAM de puntos y concesiones; GWSa complementa la lectura regional."),
        ("IRCA", "Pendiente", "No se ha incorporado una base georreferenciada de calidad del agua."),
        ("Hidrogeoquímica", "Pendiente", "No hay muestras hidrogeoquímicas integradas en esta versión."),
        ("Monitoreo", "En proceso", "Queda preparado para integrar sondas y series validadas."),
    ],
    "La Paz": [
        ("Identificación y contexto", "Completo", "Sede de La Paz, coordenadas y síntesis territorial incorporadas."),
        ("Cartografía e hidrología", "Pendiente", "Falta incorporar cartografía temática regional validada."),
        ("Clima", "En proceso", "La sección NASA POWER se activa automáticamente al detectar el Excel procesado."),
        ("Geología", "Pendiente", "Falta incorporar cartografía geológica de referencia."),
        ("Cobertura y relieve", "Pendiente", "Faltan capas de cobertura, relieve o pendientes."),
        ("Estaciones y calidad", "En proceso", "Queda habilitado el inventario de datos y fuentes."),
        ("Hidrogeología", "En proceso", "Se incorpora GWSa satelital cuando está disponible el NetCDF GRACE/GLDAS."),
        ("IRCA", "Pendiente", "No se ha incorporado una base georreferenciada de calidad del agua."),
        ("Hidrogeoquímica", "Pendiente", "No hay muestras hidrogeoquímicas integradas en esta versión."),
        ("Monitoreo", "En proceso", "Queda preparado para integrar sondas y series validadas."),
    ],
}

METADATOS_MAPAS = {
    "Leticia": {
        "hidrografia": {
            "entidad": "Instituto SINCHI",
            "producto": "Mapa de hidrografía del municipio de Leticia",
            "alcance": "Municipal y regional",
            "actualidad": "Según el documento cartográfico original",
            "limitacion": "No representa exclusivamente el radio inmediato de la Sede Amazonia.",
        },
        "humedales": {
            "entidad": "Corpoamazonia",
            "producto": "Humedales de Leticia y Puerto Nariño",
            "alcance": "Regional",
            "actualidad": "Según el documento cartográfico original",
            "limitacion": "Incluye humedales ubicados fuera del área principal del prototipo.",
        },
        "inundacion": {
            "entidad": "Corpoamazonia",
            "producto": "Áreas de inundación en la zona urbana de Leticia",
            "alcance": "Zona urbana",
            "actualidad": "Según el documento cartográfico original",
            "limitacion": "Debe interpretarse con la escala y metodología de la fuente.",
        },
        "geologia": {
            "entidad": "Instituto SINCHI",
            "producto": "Unidades geológicas del Trapecio Sur",
            "alcance": "Regional",
            "actualidad": "Información geológica regional",
            "limitacion": "No corresponde a una cartografía detallada exclusiva de la sede.",
        },
        "cobertura": {
            "entidad": "Instituto SINCHI",
            "producto": "Coberturas de la tierra del municipio de Leticia",
            "alcance": "Municipal",
            "actualidad": "Consultar el año visible en el mapa original",
            "limitacion": "Se usa como referencia; no debe interpretarse automáticamente como cobertura actual.",
        },
        "relieve": {
            "entidad": "Instituto SINCHI",
            "producto": "Geomorfología del Trapecio Sur",
            "alcance": "Regional",
            "actualidad": "Según el documento cartográfico original",
            "limitacion": "No reemplaza un DEM ni un cálculo de pendientes alrededor de la sede.",
        },
        "pozos_irca": {
            "entidad": "SENA",
            "producto": "Recurso académico de pozos y calidad del agua",
            "alcance": "Municipio de Leticia",
            "actualidad": "Recurso académico consultado para el prototipo",
            "limitacion": "Los resultados representan puntos y periodos específicos; no todo el municipio.",
        },
    },
    "Tumaco": {
        "hidrografia": {
            "entidad": "Parques Nacionales Naturales de Colombia",
            "producto": "Sistemas hídricos de Tumaco y Bajo Mira",
            "alcance": "Regional y marino-costero",
            "actualidad": "Según el documento cartográfico original",
            "limitacion": "No representa únicamente el entorno de la Sede Tumaco.",
        },
        "manglares": {
            "entidad": "CORPONARIÑO y entidades participantes",
            "producto": "Distribución regional de manglares en Nariño",
            "alcance": "Departamental y regional",
            "actualidad": "Consultar el año visible en el mapa original",
            "limitacion": "Debe utilizarse como referencia histórica y regional.",
        },
        "inundacion": {
            "entidad": "CORPONARIÑO – POMCA Río Mira",
            "producto": "Amenaza por inundación en la cuenca del río Mira",
            "alcance": "Cuenca hidrográfica",
            "actualidad": "Según el POMCA consultado",
            "limitacion": "La amenaza depende de la metodología, escala y periodo del estudio.",
        },
        "geologia": {
            "entidad": "CORPONARIÑO – POMCA Río Mira",
            "producto": "Unidades geológicas de la cuenca del río Mira",
            "alcance": "Cuenca hidrográfica",
            "actualidad": "Según el POMCA consultado",
            "limitacion": "Es un contexto geológico regional, no una cartografía de detalle de la sede.",
        },
        "cobertura": {
            "entidad": "CORPONARIÑO – POMCA Río Mira",
            "producto": "Cobertura y uso actual de la tierra",
            "alcance": "Cuenca hidrográfica",
            "actualidad": "Consultar el año visible en el mapa original",
            "limitacion": "Incluye sectores de la cuenca fuera del área inmediata de Tumaco.",
        },
        "relieve": {
            "entidad": "CORPONARIÑO – POMCA Río Mira",
            "producto": "Pendientes de la cuenca hidrográfica del río Mira",
            "alcance": "Cuenca hidrográfica",
            "actualidad": "Según el POMCA consultado",
            "limitacion": "No reemplaza un DEM recortado específicamente a la sede.",
        },
    },
    "Medellín": {
        "geologia": {
            "entidad": "Servicio Geológico Colombiano (SGC)",
            "producto": "Plancha geológica 228 – Medellín",
            "alcance": "Regional, escala 1:100.000",
            "actualidad": "Según la edición de la plancha consultada",
            "limitacion": "Es cartografía regional y no reemplaza estudios geotécnicos o geológicos de detalle de la sede.",
        },
        "estructura_ecologica": {
            "entidad": "Alcaldía de Medellín – Plan de Ordenamiento Territorial (POT)",
            "producto": "Estructura Ecológica Principal",
            "alcance": "Municipio de Medellín",
            "actualidad": "Según el POT y la cartografía consultada",
            "limitacion": "Se utiliza como contexto ambiental municipal; no corresponde a una capa exclusiva de la sede.",
        },
        "inundacion": {
            "entidad": "Alcaldía de Medellín – Plan de Ordenamiento Territorial (POT)",
            "producto": "Amenaza por inundaciones",
            "alcance": "Municipio de Medellín",
            "actualidad": "Según el POT y la cartografía consultada",
            "limitacion": "La amenaza debe interpretarse según la escala, metodología y fecha de la fuente.",
        },
    },
    "San Andrés": {
        "geologia": {
            "entidad": "CORALINA",
            "producto": "Conformación geológica de la isla de San Andrés",
            "alcance": "Isla de San Andrés",
            "actualidad": "Figura 3 del documento de cuencas hidrográficas consultado",
            "limitacion": "La lectura debe respetar la escala y clasificación del documento original.",
        },
        "vulnerabilidad_acuifero": {
            "entidad": "CORALINA",
            "producto": "Vulnerabilidad de las rocas que conforman los acuíferos",
            "alcance": "Isla de San Andrés",
            "actualidad": "Figura 4 del documento consultado",
            "limitacion": "Representa vulnerabilidad hidrogeológica regional y no sustituye evaluación puntual del acuífero.",
        },
        "nitratos": {
            "entidad": "CORALINA",
            "producto": "Concentraciones de nitratos en aguas subterráneas",
            "alcance": "Cuenca / isla de San Andrés",
            "actualidad": "Figura 9 del documento consultado",
            "limitacion": "Los valores corresponden al periodo y puntos de muestreo de la fuente original.",
        },
        "microcuencas": {
            "entidad": "CORALINA",
            "producto": "Principales microcuencas y arroyos estacionales",
            "alcance": "Isla de San Andrés",
            "actualidad": "Figura 11 del documento consultado",
            "limitacion": "El mapa representa drenajes estacionales y límites de microcuenca según la fuente original.",
        },
    },
    "Arauca": {
        "demanda_industria": {
            "entidad": "IDEAM",
            "producto": "Demanda de agua de la industria manufacturera por departamento",
            "alcance": "Nacional, con lectura departamental",
            "actualidad": "2021",
            "limitacion": "Es un indicador departamental; no representa la demanda puntual del municipio ni de la Sede Orinoquía.",
        },
        "vertimientos_industria": {
            "entidad": "IDEAM",
            "producto": "Vertimientos de aguas residuales de la industria manufacturera",
            "alcance": "Nacional, con lectura departamental",
            "actualidad": "2021",
            "limitacion": "La información es agregada por departamento y debe interpretarse como contexto de presión sobre el recurso hídrico.",
        },
        "anomalia_oferta_alta": {
            "entidad": "IDEAM – Estudio Nacional del Agua",
            "producto": "Anomalía de la Oferta Hídrica Superficial en condiciones altas",
            "alcance": "Nacional por unidades hidrográficas",
            "actualidad": "ENA 2014",
            "limitacion": "Es una referencia histórica de escala nacional y no sustituye un análisis hidrológico local actualizado de Arauca.",
        },
        "puntos_agua_subterranea": {
            "entidad": "IDEAM – Estudio Nacional del Agua",
            "producto": "Distribución de puntos de agua subterránea por Autoridad Ambiental",
            "alcance": "Nacional por autoridad ambiental",
            "actualidad": "ENA 2014",
            "limitacion": "Representa el número de puntos inventariados por autoridad ambiental, no la ubicación individual de cada pozo o aljibe.",
        },
        "volumen_concesionado": {
            "entidad": "IDEAM – Estudio Nacional del Agua",
            "producto": "Volúmenes de agua subterránea concesionada objeto de cobro TUA",
            "alcance": "Nacional",
            "actualidad": "ENA 2014",
            "limitacion": "Es información histórica agregada; no equivale a extracción real actual ni a disponibilidad del acuífero.",
        },
        "criterio_hidrogeologico": {
            "entidad": "Servicio Geológico Colombiano – PEXAS",
            "producto": "Programa de Exploración de Aguas Subterráneas – criterio de demanda e hidrogeológico",
            "alcance": "Regional, con visualización sobre Arauca y departamentos vecinos",
            "actualidad": "2005",
            "limitacion": "La capa es de planificación y exploración regional y no reemplaza una caracterización hidrogeológica local del sistema acuífero.",
        },
        "geologia": {
            "entidad": "Servicio Geológico Colombiano (SGC)",
            "producto": "Mapa Geológico de Colombia 2023",
            "alcance": "Nacional",
            "actualidad": "2023",
            "limitacion": "La escala nacional sirve como contexto regional; para la sede se requiere cartografía geológica de mayor detalle.",
        },
        "sistema_acuifero": {
            "entidad": "IDEAM",
            "producto": "SAP3.3 Sistema Acuífero Arauca-Arauquita",
            "alcance": "Arauca-Arauquita",
            "actualidad": "Anexo 7 de Aguas Subterráneas consultado",
            "limitacion": "La propia ficha reporta información hidrogeológica local limitada y varios campos como NRI; debe presentarse como delimitación y antecedente, no como caracterización completa.",
        },
    },
}

FUENTES_CLIMATICAS = pd.DataFrame({
    "Variable": [
        "Precipitación", "Temperatura media", "Temperaturas extremas",
        "Humedad relativa", "Viento", "Presión", "Radiación",
    ],
    "Leticia": [
        "NASA POWER", "NASA POWER", "NASA POWER", "NASA POWER",
        "NASA POWER", "NASA POWER", "NASA POWER",
    ],
    "Tumaco": [
        "IDEAM principal; NASA compara",
        "IDEAM principal; NASA complementa",
        "IDEAM con cautela; NASA complementa",
        "NASA + contraste IDEAM parcial",
        "NASA POWER", "NASA POWER", "NASA POWER",
    ],
    "Medellín": [
        "NASA POWER", "NASA POWER", "NASA POWER", "NASA POWER",
        "NASA POWER", "NASA POWER", "NASA POWER",
    ],
    "San Andrés": [
        "NASA POWER", "NASA POWER", "NASA POWER", "NASA POWER",
        "NASA POWER", "NASA POWER", "NASA POWER",
    ],
})

__all__ = ['MESES', 'UNAL_SEDES', 'TERRITORIOS', 'ESTADO_COMPONENTES', 'METADATOS_MAPAS', 'FUENTES_CLIMATICAS']


# En Streamlit, los módulos importados persisten entre ejecuciones.
# Se restablece el inventario antes de volver a calcular la disponibilidad.
from copy import deepcopy
_ESTADO_COMPONENTES_ORIGINAL = deepcopy(ESTADO_COMPONENTES)

def restablecer_estados_componentes():
    ESTADO_COMPONENTES.clear()
    ESTADO_COMPONENTES.update(deepcopy(_ESTADO_COMPONENTES_ORIGINAL))

__all__.append("restablecer_estados_componentes")
