# SIAMS · Integración de hidrogeoquímica del taller (2026)

Complemento **nativo de Streamlit** para el proyecto SIAMS. Se basa en los cinco ZIP del taller entregados por Adriana Patricia Piña, en especial el núcleo Python original `05_construccion/hq.py`. El código científico se conserva en `siams/hidrogeoquimica_nucleo.py`; la interfaz, las validaciones y los diagramas son componentes nuevos. No necesita incrustar el HTML original.

## Cómo instalar en Windows (VS Code)

1. Comprueba que estás trabajando con tu rama de SIAMS y que GRACE funciona. Puedes hacer un commit de respaldo antes de integrar.
2. **Extrae el contenido de este ZIP a la carpeta principal del repositorio**, junto a `app.py`. **Fusiona** la carpeta `siams` existente: no la borres ni la reemplaces por una carpeta vacía. Mantén las rutas relativas que trae el ZIP.
3. Abre la terminal **en la carpeta donde está `app.py`**, no dentro de `Datos_Hidrogeoquimica`:

   ```powershell
   python integrar_hidrogeoquimica.py
   python -m pip install -r requirements.txt
   python -m streamlit run app.py
   ```

4. Abre **Leticia → Subsuelo y calidad del agua → Hidrogeoquímica**. Verás el nuevo aplicativo (no el texto antiguo de «diagramas futuros»).
5. Prueba las cinco pestañas. Para verificar los cálculos y la integración sin instalar pytest:

   ```powershell
   python -m unittest discover -s tests -p test_hidrogeoquimica.py -v
   ```

6. Solo después de comprobar la página, haz el commit/push a la rama de revisión. El integrador deja una copia de `app.py` en `.siams_backups/` y la agrega a `.gitignore` (no debes subir esa copia).

**Importante:** `integrar_hidrogeoquimica.py` hace un cambio preciso en el bloque `elif seccion == "Hidrogeoquímica"` de `app.py` y mantiene la sección original en otras sedes (incluyendo el mapa de San Andrés). No modifica `siams/grace.py`, `siams/grace_leticia.py`, `siams/estilos.py`, `Datos_GRACE_Leticia/` ni el resto de SIAMS. Si la estructura local no coincide, el integrador **se detiene sin modificar `app.py`**.

## Estructura del complemento

```
app.py                              # ya existente: se actualizará con el integrador
integrar_hidrogeoquimica.py
siams/
    hidrogeoquimica.py             # UI en Streamlit: conserva los estilos globales
    hidrogeoquimica_datos.py       # lectura, validación y análisis de datos
    hidrogeoquimica_nucleo.py      # ecuaciones originales del taller (hq.py)
Datos_Hidrogeoquimica/
    siams_fq_largo.csv             # 223 determinaciones, 9 muestras, 4 grupos de Leticia
    gibbs_envelope.json            # envolvente empleada en Gibbs
Recursos_Hidrogeoquimica/
    Guia_taller_informes_fisicoquimicos_SIAMS.pdf
    SIAMS_fisicoquimicos_plantilla.xlsx
tests/
    test_hidrogeoquimica.py
```

## Qué permite hacer

- **Panorama:** IRCA base y límite superior condicionado por resultados no concluyentes, tabla de muestras, control aproximado de conductividad.
- **Calculadora:** detalle de cumplimiento por parámetro, carbonatos desde alcalinidad y pH, balance iónico y Na+K *inferidos*. No se presentan como análisis medidos.
- **Diagramas:** Piper y Stiff interactivos; Gibbs con envolvente de la herramienta original cuando hay datos de sólidos. Se muestran advertencias metodológicas.
- **Evolución temporal:** parámetros por punto, meses y campañas, signos `<LD` diferenciados.
- **Datos y método:** descargas de los datos y el resumen CSV, más guía PDF y plantilla XLSX.
- **Otros archivos:** lector CSV o XLSX en formato largo, escenario exploratorio de nitratos como NO3, ingreso manual de una muestra desde la página. La nueva interfaz aparece inicialmente en Leticia. Extenderla a las otras sedes es una modificación posterior del menú.

## Formato del archivo que puede cargar el usuario

La hoja de Excel puede llamarse `datos_largo` (recomendado) o cualquier otro nombre si incluye estas columnas:

```
informe,sede,punto,grupo_punto,fecha_uso,parametro,valor,signo,unidad
39915,Leticia,UN-LE-025,POZO_UN,2026-06-18,ph,6.17,,Unidades
39915,Leticia,UN-LE-025,POZO_UN,2026-06-18,alcalinidad,20,,mg/L CaCO3
```

Columnas mínimas: `informe`, `parametro`, `valor`. Otras columnas se completan con etiquetas explícitas de «no especificado». No se convierten automáticamente unidades sin metadatos. Los nitratos se interpretan inicialmente como **mg/L N–NO₃**, como en el informe original; una alternativa visible permite probar el caso NO₃⁻. `<LD` se trata como intervalo en IRCA y con regla configurable en cálculos iónicos.

## Advertencias científicas importantes

- Los resultados originales son de **agua cruda**: calcular IRCA en esta vista **no certifica potabilidad** ni sustituye una evaluación oficial de agua destinada a consumo humano.
- Las tres campañas de 2026 no justifican hablar de tendencias estadísticamente robustas.
- El perfil iónico original no incluye mediciones directas de sodio ni potasio; el **Na+K por diferencia es un supuesto gráfico**, y un cierre inducido no valida el balance.
- Se conserva el campo `bandera` sobre discrepancias de fechas, tipo de muestra, identificación, y fuentes secundarias.
- La selección de píxeles GRACE, las sondas y los análisis hidrogeológicos preexistentes **no se ven alterados**.
- Los valores ingresados/subidos desde el navegador se procesan en la sesión; no se guardan automáticamente en el repositorio ni se convierten en públicos. La base incluida sí queda en el repositorio al subirla.
- La publicación de los datos originales se realiza bajo la autorización indicada por los responsables del proyecto; conservar los alcances del acuerdo y la atribución.

## Verificación realizada

- **11 pruebas de unidad exitosas** para datos, IRCA, bicarbonatos, balance y parche idempotente.
- Lectura de los 223 resultados tanto del CSV original como del Excel original.
- Ensayo de construcción y serialización de las cuatro figuras Plotly (Piper, Stiff, Gibbs, IRCA).
- **Pendiente**: prueba visual dentro de tu instalación local de Streamlit con el `app.py` actualizado. No se ha realizado ninguna operación en tu ordenador ni se ha enviado un commit/push a GitHub.
