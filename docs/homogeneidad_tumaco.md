# Homogeneidad de la lluvia IDEAM en Tumaco (COCO EL, 51030020)

*Nota técnica que responde a la observación 3.2.a / A1 de la revisión. Octubre de 2026.*

## Qué se encontró

La aplicación reportaba para Tumaco una tendencia de lluvia de **+56,1 mm/año, creciente significativa**
(1985–2024). Al revisar la serie diaria (`P_diaria` de `ANALISIS_HIDROMETEOROLOGICO_Tumaco (2).xlsx`):

1. **Cambió la forma de registro.** Entre 1985 y 1993, entre el 51 % y el 96 % de los días con lluvia se anotaron
   con decimales (p. ej. 3,4 mm); en 1994 el 21 %; desde 1995, **ninguno**. Eso indica un cambio de observador,
   de instrumento, de procedimiento o de digitación.
2. **Cambió el nivel de la serie.** La lámina media por día lluvioso pasa de ~11 mm a ~19 mm, y el total anual
   medio de ~1.570 mm (1985–1991) a ~3.740 mm (2015–2024). 2023 suma 5.976 mm y 2024, 5.368 mm.
3. **Las pruebas de punto de cambio lo confirman** sobre la serie anual (años con ≥ 75 % de días):

| Prueba | Resultado 1985–2024 |
|---|---|
| Pettitt (1979) | p = 0,0006; primer año del nuevo segmento: 1998 |
| SNHT (Alexandersson), p por Monte Carlo (semilla fija) | p = 0,0005 |
| Mann-Kendall | τ = 0,47; p = 0,00002 |
| Mann-Kendall modificado (Hamed y Rao, 1998) | p = 0,00047 |
| Pendiente de Sen | +56,1 mm/año |

El salto en la serie *anual* aparece hacia 1998, tres años después del cambio de resolución (1995): con
una serie tan variable las pruebas ubican el cambio de nivel con incertidumbre de algunos años. Se usa
**1995** como inicio del tramo homogéneo porque es el cambio documentado en los datos diarios.

## Tramo 1995–2024

| Prueba | Resultado |
|---|---|
| Mann-Kendall | τ = 0,21; p = 0,108 |
| Hamed-Rao | p = 0,190 |
| Pendiente de Sen | +34,4 mm/año (no significativa) |
| Pettitt | p = 0,25 (sin cambio) |
| SNHT | p = 0,0005, empujado por 2023–2024 |

## Conclusión

- La tendencia 1985–2024 **no es concluyente**: puede ser, en buena parte, un artefacto del cambio de registro.
- En el tramo 1995–2024 **no hay tendencia significativa** al 5 %.
- Los años 2023–2024 son extraordinariamente altos y deben verificarse (¿El Niño/La Niña?, ¿errores de digitación?,
  ¿acumulados de varios días?).

## Qué se hizo en el código

- Los datos crudos **no se modificaron**.
- `siams/estadistica.py`: Pettitt, SNHT, Mann-Kendall con empates, Hamed-Rao y Sen (verificados contra
  `pymannkendall` 1.4.3 y `pyhomogeneity`).
- `siams/calidad.py`: registro de la serie inhomogénea con su evidencia.
- La app muestra la advertencia, las columnas de homogeneidad y la fila del tramo homogéneo.
- `scripts/03_tendencias_homogeneidad.py` regenera la tabla `docs/tendencias_homogeneidad.csv` para todas las sedes.

## Pendiente para el semillero

1. Revisar en DHIME la hoja de vida de la estación 51030020 (cambios de instrumento, traslado, observador).
2. Comparar con estaciones vecinas (p. ej. CCCP DEL PACÍFICO 51035020 si tiene lluvia; otras del Pacífico
   nariñense) mediante dobles masas o razones anuales.
3. Comparar con CHIRPS (Funk et al., 2015) e IMERG en el píxel de Tumaco.
4. Verificar los registros diarios de 2023–2024.
5. Si se confirma la causa, decidir con el docente si se ajusta el tramo previo (por ejemplo con razones con una
   estación de referencia) o si se trabaja solo con 1995 en adelante. Cualquier ajuste debe guardarse como serie
   **derivada**, nunca sobre los datos crudos.
