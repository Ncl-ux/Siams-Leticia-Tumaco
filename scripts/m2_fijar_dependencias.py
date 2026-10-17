#!/usr/bin/env python3
r"""M2: fija versiones instaladas, sin actualizar paquetes ni alterar datos de SIAMS.

Uso en el proyecto SIAMS, con su entorno virtual activo:
    .\.venv\Scripts\python.exe scripts\m2_fijar_dependencias.py
    .\.venv\Scripts\python.exe scripts\m2_fijar_dependencias.py --verificar
"""
from __future__ import annotations

import argparse
from collections import OrderedDict, deque
from dataclasses import dataclass, field
from importlib import metadata
from pathlib import Path
import subprocess
import sys

try:
    from packaging.requirements import Requirement
    from packaging.utils import canonicalize_name
except ImportError:
    # pip incluye packaging para analizar dependencias en un entorno recién creado.
    from pip._vendor.packaging.requirements import Requirement
    from pip._vendor.packaging.utils import canonicalize_name

RAIZ = Path(__file__).resolve().parents[1]
ARCHIVOS = (
    "requirements.txt",
    "requirements_hidrogeoquimica.txt",
    "requirements-dev.txt",
)
LOCK = "requirements-lock.txt"
# Importaciones utilizadas en módulos de SIAMS no declaradas en el requirements antiguo.
ADICIONES_RUNTIME = ("Pillow", "pypdfium2")


@dataclass
class Dependencia:
    nombre: str
    extras: set[str] = field(default_factory=set)
    marcador: str | None = None


def _leer(nombre: str) -> OrderedDict[str, Dependencia]:
    ruta = RAIZ / nombre
    if not ruta.is_file():
        raise ValueError(f"No se encontró {ruta}. Ejecuta el script en el repositorio SIAMS.")
    resultado: OrderedDict[str, Dependencia] = OrderedDict()
    for n, original in enumerate(ruta.read_text(encoding="utf-8-sig").splitlines(), 1):
        linea = original.strip()
        if not linea or linea.startswith("#"):
            continue
        if linea.startswith("-") or " @ " in linea:
            raise ValueError(f"{nombre}:{n}: requisito no estándar; revisar sin sobrescribir: {linea}")
        try:
            req = Requirement(linea)
        except Exception as exc:
            raise ValueError(f"{nombre}:{n}: no se pudo interpretar {linea!r}: {exc}") from exc
        clave = canonicalize_name(req.name)
        if req.specifier and not req.specifier.contains(_version(req.name)[1], prereleases=True):
            raise ValueError(
                f"{nombre}:{n}: {req.name} instalado no cumple el intervalo original {req.specifier}"
            )
        marcador = str(req.marker) if req.marker else None
        if clave not in resultado:
            resultado[clave] = Dependencia(req.name, set(req.extras), marcador)
        else:
            previo = resultado[clave]
            if previo.marcador != marcador:
                raise ValueError(f"{nombre}: condiciones incompatibles para {req.name}; revisar manualmente.")
            previo.extras.update(req.extras)
    return resultado


def _version(nombre: str) -> tuple[str, str]:
    try:
        dist = metadata.distribution(nombre)
    except metadata.PackageNotFoundError as exc:
        raise ValueError(
            f"Falta instalar {nombre} en este .venv. Ejecuta primero las pruebas, "
            f"revisa requirements.txt e instala la dependencia necesaria antes de fijar M2."
        ) from exc
    return str(dist.metadata.get("Name", nombre)), dist.version


def _fijado(dep: Dependencia) -> str:
    nombre, version = _version(dep.nombre)
    extras = "[" + ",".join(sorted(dep.extras)) + "]" if dep.extras else ""
    condicion = " ; " + dep.marcador if dep.marcador else ""
    return f"{nombre}{extras}=={version}{condicion}"


def _grafo_bloqueado(raices: dict[str, Dependencia]) -> tuple[list[str], int]:
    """Cierra recursivamente Requires-Dist respetando los extras y markers locales."""
    extras_por_paquete: dict[str, set[str]] = {k: set(v.extras) for k, v in raices.items()}
    nombres: dict[str, str] = {k: v.nombre for k, v in raices.items()}
    procesado: dict[str, frozenset[str]] = {}
    pendientes = deque(raices)
    while pendientes:
        clave = pendientes.popleft()
        extras = extras_por_paquete[clave]
        if procesado.get(clave) == frozenset(extras):
            continue
        procesado[clave] = frozenset(extras)
        dist = metadata.distribution(nombres[clave])
        for requisito in dist.requires or ():
            req = Requirement(requisito)
            # Una dependencia puede aplicar al paquete base o a alguno de sus extras.
            aplica = req.marker is None or any(
                req.marker.evaluate({"extra": extra}) for extra in ({""} | extras)
            )
            if not aplica:
                continue
            subclave = canonicalize_name(req.name)
            nuevo = set(req.extras)
            if subclave not in extras_por_paquete:
                extras_por_paquete[subclave] = nuevo
                nombres[subclave] = req.name
                pendientes.append(subclave)
            elif not nuevo.issubset(extras_por_paquete[subclave]):
                extras_por_paquete[subclave].update(nuevo)
                pendientes.append(subclave)
    fijados = []
    for clave in sorted(nombres):
        nombre, version = _version(nombres[clave])
        fijados.append(f"{nombre}=={version}")
    return fijados, len(fijados)


def _desglose() -> tuple[OrderedDict[str, Dependencia], OrderedDict[str, Dependencia], OrderedDict[str, Dependencia]]:
    runtime, hidro, dev = (_leer(n) for n in ARCHIVOS)
    for nombre in ADICIONES_RUNTIME:
        clave = canonicalize_name(nombre)
        if clave not in runtime:
            runtime[clave] = Dependencia(nombre)
    if not runtime:
        raise ValueError("requirements.txt está vacío")
    if not dev:
        raise ValueError("requirements-dev.txt está vacío")
    return runtime, hidro, dev


def _analizar_archivo(nombre: str) -> dict[str, str]:
    ruta = RAIZ / nombre
    if not ruta.exists():
        raise ValueError(f"Falta {nombre}")
    fijados: dict[str, str] = {}
    for linea in ruta.read_text(encoding="utf-8-sig").splitlines():
        linea = linea.strip()
        if not linea or linea.startswith("#"):
            continue
        req = Requirement(linea)
        spec = list(req.specifier)
        if len(spec) != 1 or spec[0].operator != "==" or spec[0].version.endswith(".*"):
            raise ValueError(f"{nombre}: no está fijado a una versión exacta: {linea}")
        clave = canonicalize_name(req.name)
        if clave in fijados:
            raise ValueError(f"{nombre}: dependencia duplicada: {req.name}")
        fijados[clave] = spec[0].version
    return fijados


def verificar() -> None:
    fijados = {nombre: _analizar_archivo(nombre) for nombre in (*ARCHIVOS, LOCK)}
    directos = {clave: version for archivo in ARCHIVOS for clave, version in fijados[archivo].items()}
    for clave, v in directos.items():
        if fijados[LOCK].get(clave) != v:
            raise ValueError(f"Lock desactualizado o faltante para {clave}=={v}")
        _, instalada = _version(clave)
        if instalada != v:
            raise ValueError(f"Versión local diferente para {clave}: requisito {v}, instalada {instalada}")
    print(f"M2 verificado: {len(directos)} dependencias directas fijadas, "
          f"{len(fijados[LOCK])} paquetes en el lock; Python {sys.version.split()[0]}.")


def generar() -> None:
    if sys.version_info[:2] != (3, 12):
        raise ValueError(
            f"Tu Python es {sys.version_info.major}.{sys.version_info.minor}. "
            "SIAMS CI utiliza Python 3.12: genera M2 con el .venv de Python 3.12."
        )
    if sys.prefix == sys.base_prefix:
        raise ValueError("No se detectó un entorno virtual. Usa .venv\\Scripts\\python.exe.")
    runtime, hidro, dev = _desglose()
    # Comprueba primero que el entorno actual no presente conflictos de dependencias.
    chequeo = subprocess.run(
        [sys.executable, "-m", "pip", "check"],
        text=True, capture_output=True, check=False,
    )
    if chequeo.returncode != 0:
        raise ValueError("pip check detectó conflictos. Corrígelos antes de congelar M2:\n"
                         + (chequeo.stdout + chequeo.stderr).strip())
    raices: dict[str, Dependencia] = {}
    for deps in (runtime, hidro, dev):
        for clave, req in deps.items():
            if clave not in raices:
                raices[clave] = Dependencia(req.nombre, set(req.extras))
            else:
                raices[clave].extras.update(req.extras)
    lock, nlock = _grafo_bloqueado(raices)
    archivos: dict[str, str] = {}
    for nombre, dependencias in zip(ARCHIVOS, (runtime, hidro, dev)):
        comentario = (
            f"# SIAMS M2: dependencias directas fijadas con el .venv del proyecto.\n"
            f"# Python {sys.version_info.major}.{sys.version_info.minor}; "
            "no actualizar sin ejecutar pruebas.\n"
        )
        archivos[nombre] = comentario + "\n".join(_fijado(dep) for dep in dependencias.values()) + "\n"
    archivos[LOCK] = (
        "# SIAMS M2: cierre de dependencias directas y transitivas del .venv local.\n"
        f"# Generado con Python {sys.version.split()[0]}; plataforma {sys.platform}.\n"
        "# No instalar directamente en Linux/Streamlit Cloud sin validar compatibilidad.\n"
        "# Despliegue multiplataforma: requirements.txt.\n"
        + "\n".join(lock) + "\n"
    )
    # Todo se resuelve/verifica antes de modificar un solo archivo.
    for nombre, contenido in archivos.items():
        (RAIZ / nombre).write_text(contenido, encoding="utf-8", newline="\n")
    verificar()
    print("No se instaló ni actualizó ningún paquete.")
    print("Revisa git diff, ejecuta pytest y confirma el despliegue antes del commit.")
    print(f"Paquetes del lock: {nlock}.")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--verificar", action="store_true", help="Valida versiones, sin modificar archivos")
    args = parser.parse_args()
    try:
        verificar() if args.verificar else generar()
    except (ValueError, metadata.PackageNotFoundError) as exc:
        print(f"ERROR M2: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
