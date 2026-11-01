# Actualización de sedes 2026 (rama `actualizacion-sedes-2026`)

## Qué se integró
| Componente | Archivos | Script |
|---|---|---|
| Niveles de agua subterránea (Arauca, La Paz, Leticia, Tumaco, Bogotá) | `data/processed/niveles/` | `scripts/10_niveles_sedes.py` |
| Fisicoquímica Arauca (4 muestreos 2025) y Tumaco (2015–2025) + iones meq/L | `data/processed/hidrogeoquimica/fq_sedes_*.csv` | `scripts/11_fisicoquimica_sedes.py` (requiere `FQSIAMS_PATH`) |
| Pruebas de bombeo Arauca (ECOLAVF 2025) y La Paz (HGM 2020) con cita y página | `data/processed/bombeo/resumen_pruebas_bombeo.csv` | transcripción manual |
| Isótopos en precipitación (base nacional IDEAM; Bogotá IAEA/GNIP) | `data/processed/isotopos/isotopos_ideam_tidy.csv` | — |
| Esquema y validador de datos de campo (app offline XUE Hub) | `config/esquema_datos_campo.csv`, `siams/datos_campo.py` | `scripts/validar_datos_campo.py` |
| Actualización semanal NASA POWER, CHIRPS v3.0, IDEAM (datos.gov.co) | `data/processed/actualizacion/` | `scripts/12_actualizacion_semanal.py`, `.github/workflows/actualizacion_semanal.yml` |

## Cota del nivel de agua
* Cota del terreno = Copernicus DEM GLO-30 − 1,5 m (sesgo estimado en Leticia), salvo cota levantada (ninguna disponible aún).
* Cota del nivel = cota del terreno − profundidad del agua.
* Sondas de presión: profundidad = profundidad del sensor − carga sobre el sensor. Keller (Leticia, Arauca, La Paz, Bogotá) compensadas internamente; Diver de Tumaco compensado con el barómetro EP979.
* Profundidad del sensor conocida: Numae 17 m (dato del proyecto); Tumaco: longitud de cable 13,00 m medida desde el brocal (una exportación dice 1,30 m: se tomó como error de digitación). Desconocida: SONDA05 (Arauca), SONDA04 (La Paz), SONDA_01/SONDA_02 (Leticia) → solo se publica la columna de agua, sin cota. Se completa en `config/pozos_monitoreo.csv`.
* Banderas: `sensor_fuera_del_agua` (< 0,05 m; < 0,3 m en Tumaco) y `descenso_brusco_posible_bombeo` (> 2 m bajo la mediana móvil de 7 días). No se borran: la app las oculta por defecto.
* Tumaco usa las coordenadas de la sede (no hay coordenada del pozo).

## Fuentes desactivadas en la automatización
GRACE/GLDAS (credenciales Earthdata) y ERA5-Land (clave Copernicus CDS): pasos comentados en el workflow.

## Datos de uso interno
El paquete `fqsiams` dice «Uso confidencial»: no se versiona aquí; solo se publican las tablas derivadas.

## Bogotá
Niveles, isótopos del campus y fisicoquímica de laboratorio salen del paquete ordenado preparado el 2026-11-01
(`scripts/10b_niveles_bogota_paquete.py`; no se reprocesan los crudos).
* Profundidad = −«nivel corregido» de la OGA (manual y automático); cota = (GLO-30 − 1,5 m) − profundidad.
  En el campus GLO-30 es un modelo de superficie (puede incluir edificios y árboles): la cota es aproximada.
* El logger crudo de PA01/PA02 (B = 32 m) se publica solo como carga sobre el sensor; el `nivel_msnm` procesado
  no se usa porque su referencia no está documentada.
* PA27 sin coordenadas; PA36 con posición distinta entre fuentes.
* Fisicoquímica (agosto de 2023): PA05 y PA25 con turbiedad y SST extremos (sin purga): no representan el acuífero.
* Isótopos: 94 muestras del campus (2022–2024) y LMWL combinada IDEAM + campus δ²H = 8,02·δ¹⁸O + 10,32.
