"""Persistencia del gestor: carga y guardado de datos en JSON."""

import json
import os
from typing import Any

import gestor


def guardar_datos(ruta: str) -> bool:
    """Guarda el inventario, las ventas y el folio actual en un JSON."""
    datos = {
        "inventario": gestor.INVENTARIO,
        "ventas": gestor.VENTAS,
        "contador": gestor.contador_ventas,
    }
    with open(ruta, "w", encoding="utf-8") as archivo:
        json.dump(datos, archivo, indent=2, ensure_ascii=False)
    return True


def _leer_json(ruta: str) -> dict[str, Any] | None:
    """Lee y valida el archivo. Regresa los datos o None si no sirve.

    Toda la validacion ocurre ANTES de tocar el estado global, para que un
    archivo danado nunca deje el inventario a medio cargar.
    """
    try:
        with open(ruta, encoding="utf-8") as archivo:
            datos: Any = json.load(archivo)
    except (json.JSONDecodeError, UnicodeDecodeError):
        gestor.ultimo_error = "archivo corrupto"
        return None
    except OSError:
        gestor.ultimo_error = "no se pudo leer el archivo"
        return None
    estructura_valida = (
        isinstance(datos, dict)
        and isinstance(datos.get("inventario"), dict)
        and isinstance(datos.get("ventas"), list)
    )
    if not estructura_valida:
        gestor.ultimo_error = "archivo corrupto"
        return None
    return dict(datos)


def cargar_datos(ruta: str) -> bool:
    """Lee el archivo JSON y deja los datos en el estado global.

    Regresa False si el archivo no existe o esta corrupto; en ese caso el
    estado actual no se modifica.
    """
    if not hay_archivo(ruta):
        gestor.ultimo_error = "el archivo no existe"
        return False
    datos = _leer_json(ruta)
    if datos is None:
        return False
    # Se mutan en sitio: otros modulos guardan referencia a estos objetos.
    gestor.INVENTARIO.clear()
    gestor.INVENTARIO.update(datos["inventario"])
    gestor.VENTAS.clear()
    gestor.VENTAS.extend(datos["ventas"])
    gestor.contador_ventas = datos.get("contador", 0)
    return True


def hay_archivo(ruta: str) -> bool:
    """Indica si ya existe el archivo de datos."""
    return os.path.exists(ruta)
