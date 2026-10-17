# SIAMS — Complemento GRACE y niveles de agua de Leticia

## Qué integra

Complemento de la **sección existente** `Subsuelo y calidad del agua → Agua subterránea (GRACE)`, exclusivo de Leticia. Se conserva el resto de GRACE (otras sedes, GGDI, mapa, climatología y productos NetCDF).

Se adapta al estilo real de `siams/estilos.py` (variables `--siams-verde` y estilos `soft-box`, `warning-box`, `interpretation-box`, métricas y pestañas). No agrega un CSS global ni cambia el tema claro/oscuro.

**Pestañas:** serie GRACE (A, B, TWSA y Zenodo); pozos/sondas (Numae, Casa del profesor Arturo, UNAL); comparación exploratoria mensual con río IDEAM; metodología y descargas CSV.

## Instalación en la rama `mejoras-revision-siams`

1. Haz una copia de seguridad o commit de tu trabajo actual.
2. Extrae el contenido del ZIP en **la raíz de tu repositorio SIAMS**, al lado de `app.py`. Si Windows pregunta si deseas fusionar la carpeta `siams`, acepta **fusionar**: solo se añade `siams/grace_leticia.py`.
3. Verifica que quede así:

   ```text
   Siams-Leticia-Tumaco/
   ├── app.py                         (ya existe)
   ├── siams/
   │   ├── estilos.py                 (sin cambios)
   │   ├── grace.py                   (sin cambios)
   │   └── grace_leticia.py          (nuevo)
   ├── Datos_GRACE_Leticia/           (nueva)
   │   ├── GWSA_A_B_sites_Leticia.csv
   │   ├── transductores_natural_diario.csv
   │   ├── Leticia_pozo_serie_natural_filtrada.csv
   │   ├── ideam_nivel_rio_mensual.csv
   │   └── GRACE_site_pixels.csv
   ├── integrar_en_app.py             (nuevo)
   └── LEEME_GRACE_LETICIA.md         (nuevo)
   ```

4. Abre la terminal de VS Code dentro de la carpeta del repositorio y ejecuta:

   ```powershell
   python integrar_en_app.py
   streamlit run app.py
   ```

   El integrador crea una copia `app.py.antes_grace_leticia.bak` y añade **solo** una importación y una llamada en la sección GRACE. Comprueba sintaxis antes de tocar el archivo. Es idempotente: ejecutarlo nuevamente no duplica el módulo.

5. En el navegador abre: **Leticia → Subsuelo y calidad del agua → Agua subterránea (GRACE)**; baja hasta el nuevo apartado **Niveles de agua y GRACE · Leticia**. Prueba los cuatro tabs y cambia de territorio para comprobar que las otras sedes permanecen iguales.

6. Si todo se ve correcto, revisa `git status` y sube solamente los archivos nuevos y `app.py`. **No subas** `app.py.antes_grace_leticia.bak` ni los 78 MB del ZIP original.

## Integración manual alternativa

Si `integrar_en_app.py` no encuentra la estructura esperada, no fuerza cambios. En ese caso:

- En `app.py`, junto a `from siams.grace import ...`, agrega:

  ```python
  from siams.grace_leticia import mostrar_grace_leticia
  ```

- Dentro de `elif seccion == "Agua subterránea (GRACE)":`, **al final del bloque**, justo antes del encabezado `# HIDROGEOQUÍMICA` y aún con cuatro espacios de sangría, agrega:

  ```python
      if territorio == "Leticia":
          mostrar_grace_leticia()
  ```

## Advertencias científicas obligatorias

- **GRACE/GRACE-FO no mide directamente profundidad de pozo.** GWSA B expresa anomalías regionales de almacenamiento en cm equivalentes de agua, no cota del acuífero. No se deduce recarga ni volumen almacenado sin parámetros físicos adicionales.
- GWSA B disponible de **abril de 2002 a junio de 2026**, con **33 meses ausentes** sin interpolar, según el producto procesado. Zenodo termina en abril de 2023.
- Numae tiene **124 días útiles** de señal filtrada de presión; está pendiente verificar la referencia instrumental. Casa del profesor Arturo tiene **31 días** de señal filtrada sin superposición temporal con GWSA B.
- Pozo UNAL: **39 mediciones manuales filtradas**; son profundidades **respecto al brocal**, no niveles absolutos con datum topográfico validado.
- Pachovela tiene lectura de prueba, insuficiente para curva de monitoreo.
- La comparación multiserie inicial (GRACE B + Numae + UNAL) tiene **solo cuatro meses** compartidos (marzo–junio de 2026); las curvas se estandarizan en esa ventana (z-score), sin afirmar correlaciones significativas.
- La celda JPL utilizada (lat -4,25; lon -69,75) está a **22,29 km** del punto de referencia de Leticia, y una cuadrícula de 0,5° no equivale a la resolución efectiva real de GRACE.
- Método B recomendado como reconstrucción; su validación r=0,99, RMSE=2,50 cm se refiere a **comparación con el producto Zenodo**, **no a exactitud frente a pozos**.

## Procedencia y mantenimiento

Se copiaron **sin recalcular** cinco CSV ya procesados en el archivo `Proyecto_GRACE_Leticia (1).zip` suministrado por la profesora. Se mantienen nombres de columnas y valores originales para trazabilidad. El módulo es únicamente de presentación, agrupación temporal y estandarización exploratoria; no reemplaza el código científico ni los datos originales.

No es necesario descargar nuevos NetCDF ni instalar paquetes fuera de los que ya utiliza SIAMS: Streamlit, pandas, numpy y Plotly. La sección satelital previa sigue usando su NetCDF habitual.
