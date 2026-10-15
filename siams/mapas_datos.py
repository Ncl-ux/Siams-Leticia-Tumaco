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

from .utilidades import resolver_carpeta_preferida

MAPAS_LETICIA = {
    "cobertura": "mapa_coberturas_leticia",
    "geologia": "mapa_geologia_trapecio_sur",
    "relieve": "mapa_geomorfologia_relieve_leticia",
    "hidrografia": "mapa_hidrografia_leticia",
    "humedales": "mapa_humedales_leticia_puerto_narino",
    "inundacion": "mapa_inundacion_urbana_leticia",
    "pozos_irca": "mapa_pozos_irca_leticia",
}

MAPAS_TUMACO = {
    "cobertura": "mapa_coberturas_tumaco",
    "geologia": "mapa_geologia_tumaco",
    "relieve": "mapa_relieve_tumaco",
    "hidrografia": "mapa_hidrografia_tumaco",
    "manglares": "mapa_manglares_tumaco",
    "inundacion": "mapa_inundacion_tumaco",
}

MAPAS_MEDELLIN = {
    "geologia": "mapa_geologia_medellin_plancha_228",
    "estructura_ecologica": "mapa_estructura_ecologica_medellin",
    "inundacion": "mapa_amenaza_inundacion_medellin",
}

MAPAS_SAN_ANDRES = {
    "geologia": "mapa_geologia_san_andres",
    "vulnerabilidad_acuifero": "mapa_vulnerabilidad_acuifero_san_andres",
    "nitratos": "mapa_nitratos_aguas_subterraneas_san_andres",
    "microcuencas": "mapa_microcuencas_arroyos_san_andres",
}

MAPAS_ARAUCA = {
    "demanda_industria": "mapa_demanda_agua_industria_manufacturera_arauca_2021",
    "vertimientos_industria": "mapa_vertimientos_industria_manufacturera_arauca_2021",
    "anomalia_oferta_alta": "mapa_anomalia_oferta_hidrica_superficial_arauca_ena2014",
    "puntos_agua_subterranea": "mapa_puntos_agua_subterranea_arauca_ena2014",
    "volumen_concesionado": "mapa_volumen_agua_subterranea_concesionada_arauca_ena2014",
    "criterio_hidrogeologico": "mapa_criterio_demanda_hidrogeologico_arauca_pexas_2005",
    "geologia": "mapa_geologico_colombia_2023_arauca",
    "sistema_acuifero": "mapa_sistema_acuifero_arauca_arauquita",
}

MAPAS_BOGOTA = {
    "ubicacion_colombia": "Bogotá 1-10000000.pdf",
    "ubicacion_region": "Bogotá 1- 1500000.pdf",
    "ubicacion_campus": "Bogotá 1- 10000.pdf",
}

MAPAS_UBICACION_QGIS = {
    "Bogotá": [
        {
            "paso": "Colombia",
            "archivo": "Bogotá 1-10000000.pdf",
            "titulo": "Nivel 1 · Colombia",
            "detalle": "Ubicación de Bogotá D.C. dentro del contexto nacional.",
            "escala": "1:10.000.000",
        },
        {
            "paso": "Bogotá",
            "archivo": "Bogotá 1- 1500000.pdf",
            "titulo": "Nivel 2 · Bogotá y contexto regional",
            "detalle": "Acercamiento al Distrito Capital y su entorno regional.",
            "escala": "1:1.500.000",
        },
        {
            "paso": "Campus",
            "archivo": "Bogotá 1- 10000.pdf",
            "titulo": "Nivel 3 · Campus Ciudad Universitaria",
            "detalle": "Detalle de la Sede Bogotá y su entorno inmediato.",
            "escala": "1:10.000",
        },
    ],
    "Arauca": [
        {
            "paso": "Colombia",
            "archivo": "Arauca 1-10000000.pdf",
            "titulo": "Nivel 1 · Colombia",
            "detalle": "Ubicación de Arauca dentro del contexto nacional.",
            "escala": "1:10.000.000",
        },
        {
            "paso": "Arauca",
            "archivo": "Arauca 1-1500000.pdf",
            "titulo": "Nivel 2 · Arauca y contexto regional",
            "detalle": "Acercamiento regional al territorio de la Sede Orinoquía.",
            "escala": "1:1.500.000",
        },
        {
            "paso": "Sede",
            "archivo": "Arauca 1-1500.pdf",
            "titulo": "Nivel 3 · Entorno de la Sede Orinoquía",
            "detalle": "Detalle cartográfico del entorno inmediato de la sede.",
            "escala": "1:1.500",
        },
    ],
    "Medellín": [
        {
            "paso": "Colombia",
            "archivo": "Medellín 1-10000000.pdf",
            "titulo": "Nivel 1 · Colombia",
            "detalle": "Ubicación de Medellín dentro del contexto nacional.",
            "escala": "1:10.000.000",
        },
        {
            "paso": "Medellín",
            "archivo": "Medellín 1-2500000.pdf",
            "titulo": "Nivel 2 · Medellín y contexto regional",
            "detalle": "Acercamiento al Valle de Aburrá y al entorno urbano de Medellín.",
            "escala": "Por verificar (archivo identificado como 1:2.500.000)",
        },
        {
            "paso": "Sede",
            "archivo": "Medellín 1-5000.pdf",
            "titulo": "Nivel 3 · Entorno de la Sede Medellín",
            "detalle": "Detalle cartográfico del entorno inmediato de la sede.",
            "escala": "1:5.000",
        },
    ],
    "San Andrés": [
        {
            "paso": "Colombia",
            "archivo": "San Andrés 1 - 10000000.pdf",
            "titulo": "Nivel 1 · Colombia",
            "detalle": "Ubicación del archipiélago de San Andrés en el contexto nacional.",
            "escala": "1:10.000.000",
        },
        {
            "paso": "Isla",
            "archivo": "San Andrés 1 - 75000.pdf",
            "titulo": "Nivel 2 · Isla de San Andrés",
            "detalle": "Aproximación cartográfica al entorno insular de San Andrés.",
            "escala": "1:75.000",
        },
    ],
    "Tumaco": [
        {
            "paso": "Colombia",
            "archivo": "Tumaco 1 - 10000000.pdf",
            "titulo": "Nivel 1 · Colombia",
            "detalle": "Ubicación de Tumaco dentro del contexto nacional.",
            "escala": "1:10.000.000",
        },
        {
            "paso": "Región",
            "archivo": "Tumaco 1 - 1500000.pdf",
            "titulo": "Nivel 2 · Pacífico nariñense",
            "detalle": "Contexto regional del territorio de Tumaco y la costa pacífica de Nariño.",
            "escala": "1:1.500.000",
        },
        {
            "paso": "Sede",
            "archivo": "Tumaco 1- 1500.pdf",
            "titulo": "Nivel 3 · Entorno de la Sede Tumaco",
            "detalle": "Detalle cartográfico de la Sede Tumaco y su entorno inmediato.",
            "escala": "1:1.500",
        },
    ],
    "Leticia": [
        {
            "paso": "Colombia",
            "archivo": "Leticia 1-8250000.pdf",
            "titulo": "Nivel 1 · Colombia",
            "detalle": "Ubicación de Leticia dentro del territorio nacional.",
            "escala": "1:8.250.000",
        },
        {
            "paso": "Amazonas",
            "archivo": "Leticia 1-5300000.pdf",
            "titulo": "Nivel 2 · Contexto amazónico",
            "detalle": "Aproximación territorial intermedia presentada en la cartografía QGIS.",
            "escala": "1:5.300.000",
        },
        {
            "paso": "Sede",
            "archivo": "Leticia 1-1400.pdf",
            "titulo": "Nivel 3 · Entorno de la Sede Amazonia",
            "detalle": "Ubicación de detalle del entorno inmediato de la sede.",
            "escala": "1:1.400",
        },
    ],
    "La Paz": [
        {
            "paso": "Colombia",
            "archivo": "La Paz 1-7500000.pdf",
            "titulo": "Nivel 1 · Colombia",
            "detalle": "Ubicación de La Paz, Cesar, dentro del territorio nacional.",
            "escala": "1:7.500.000",
        },
        {
            "paso": "Cesar",
            "archivo": "La Paz 1-2750000.pdf",
            "titulo": "Nivel 2 · La Paz y contexto regional",
            "detalle": "Aproximación regional al territorio de La Paz.",
            "escala": "1:2.750.000",
        },
        {
            "paso": "Sede",
            "archivo": "La Paz 1-3000.pdf",
            "titulo": "Nivel 3 · Entorno de la Sede de La Paz",
            "detalle": "Detalle cartográfico del entorno inmediato de la sede.",
            "escala": "1:3.000",
        },
    ],
}

FICHA_QGIS_REFERENCIA = {
    "src": "MAGNA-SIRGAS 2018 / Origen-Nacional (EPSG:9377)",
    "proyeccion": "Transversa de Mercator",
    "unidades": "Metros",
    "fuentes": "OpenStreetMap (2024) · Esri World Imagery (2023)",
    "elaboracion": "Semillero SIAMS · Cartografía académica elaborada en QGIS",
    "fecha": "2026",
}

MAPAS_POR_TERRITORIO = {
    "Bogotá": MAPAS_BOGOTA,
    "Leticia": MAPAS_LETICIA,
    "Tumaco": MAPAS_TUMACO,
    "Medellín": MAPAS_MEDELLIN,
    "San Andrés": MAPAS_SAN_ANDRES,
    "Arauca": MAPAS_ARAUCA,
    "La Paz": {},
}

def encontrar_carpeta_mapas() -> Path:
    """Devuelve la carpeta principal de mapas temáticos.

    Prioriza la carpeta renombrada ``Mapas_Tematicos`` y mantiene compatibilidad
    con el nombre anterior ``SIAMS MAPAS``.
    """
    return resolver_carpeta_preferida("Mapas_Tematicos", "SIAMS MAPAS")

CARPETA_MAPAS_QGIS = resolver_carpeta_preferida("Mapas_Qgis", "Mapas Qgis")

CARPETA_MAPAS = encontrar_carpeta_mapas()

__all__ = ['MAPAS_LETICIA', 'MAPAS_TUMACO', 'MAPAS_MEDELLIN', 'MAPAS_SAN_ANDRES', 'MAPAS_ARAUCA', 'MAPAS_BOGOTA', 'MAPAS_UBICACION_QGIS', 'FICHA_QGIS_REFERENCIA', 'MAPAS_POR_TERRITORIO', 'encontrar_carpeta_mapas', 'CARPETA_MAPAS_QGIS', 'CARPETA_MAPAS']
