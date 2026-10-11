"""Registro de problemas de calidad documentados en las series de SIAMS.

Las series NO se corrigen aquí: solo se marcan para que la app advierta y
restrinja el análisis de tendencia al tramo homogéneo. Ver
``data/README.md`` y ``docs/homogeneidad_tumaco.md``.
"""

from __future__ import annotations

SERIES_INHOMOGENEAS = {
    # (territorio, fuente, variable)
    ("Tumaco", "IDEAM", "Precipitación"): {
        "estacion": "COCO EL [51030020]",
        "anio_cambio": 1995,
        "tramo_homogeneo": (1995, 2024),
        "motivo": (
            "Cambio de resolución de registro a mediados de los noventa: entre el 51 % y el 96 % de "
            "los días con lluvia tiene decimales en 1985–1993, el 21 % en 1994 y el 0 % desde 1995. "
            "La lámina media por día lluvioso pasa de 11 mm (1985–1994) a 19 mm (1995–2024). "
            "El total anual medio pasa de ~1.570 mm (1985–1991) a ~3.740 mm (2015–2024) y 2023 "
            "suma 5.976 mm. Pettitt (p < 0,001) y SNHT (p < 0,001) ubican el salto de la serie "
            "anual hacia 1998. "
            "Hasta revisar la historia de la estación en DHIME y contrastar con estaciones "
            "vecinas y CHIRPS, la tendencia 1985–2024 se considera NO CONCLUYENTE."
        ),
    },
}


def marca_inhomogeneidad(territorio: str, fuente: str, variable: str):
    """Devuelve el registro de inhomogeneidad documentada o ``None``."""
    return SERIES_INHOMOGENEAS.get((territorio, fuente, variable))
