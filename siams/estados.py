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

from .catalogo import ESTADO_COMPONENTES, TERRITORIOS
from .mapbiomas import COBERTURAS_POR_TERRITORIO, encontrar_csv_coberturas
from .landsat import inventario_landsat

def actualizar_estado_coberturas() -> None:
    """Actualiza solo el componente de cobertura; el relieve sigue en proceso."""
    for nombre, config in COBERTURAS_POR_TERRITORIO.items():
        disponibles = [codigo for codigo in config["zonas"] if len(encontrar_csv_coberturas(nombre, codigo)["serie"]) == 1]
        if not disponibles:
            continue
        nota = "CSV de coberturas detectados para " + ", ".join(config["zonas"][codigo] for codigo in disponibles) + "; la cartografía de relieve conserva su estado previo."
        ESTADO_COMPONENTES[nombre] = [
            (componente, "En proceso", nota) if componente == "Cobertura y relieve" else (componente, estado, texto)
            for componente, estado, texto in ESTADO_COMPONENTES[nombre]
        ]

def actualizar_estado_landsat() -> None:
    """Reconoce series Landsat como producto exploratorio, sin considerarlas validadas."""
    for nombre_territorio in TERRITORIOS:
        inv = inventario_landsat(nombre_territorio)
        if not inv["gifs"]:
            continue
        detalle = (
            "Landsat: animación por fechas disponibles"
            + (", CSV de áreas" if inv["areas"] else "")
            + (" y control de escenas" if inv["control"] else "")
            + ". Producto exploratorio pendiente de validación."
        )
        ESTADO_COMPONENTES[nombre_territorio] = [
            (componente, "En proceso", detalle if estado == "Pendiente"
             else f"{nota} {detalle}")
            if componente == "Cobertura y relieve" else (componente, estado, nota)
            for componente, estado, nota in ESTADO_COMPONENTES[nombre_territorio]
        ]

__all__ = ['actualizar_estado_coberturas', 'actualizar_estado_landsat']
