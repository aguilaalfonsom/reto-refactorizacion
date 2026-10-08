# CLAUDE.md — Gestor de inventario y ventas "La Esquina"

Instrucciones para Claude Code en este repositorio. Léelas completas antes de
proponer o aplicar cualquier cambio.

## Qué es el proyecto

Aplicación de consola en Python (3.10+) para una tienda pequeña: alta de
productos, ventas con descuentos e IVA, cotizaciones, alertas de stock bajo,
reportes y persistencia en JSON. Es material de un reto de **refactorización**:
el objetivo es mejorar la calidad del código **sin cambiar su comportamiento
observable**.

```
src/gestor.py     # Reglas de negocio: productos, ventas, cotizaciones
src/almacen.py    # Persistencia JSON (guardar/cargar el estado)
src/reportes.py   # Reportes e indicadores (inventario, ventas, más vendidos)
src/main.py       # Menú interactivo de consola (única capa con input/print de menú)
tests/            # Suite pytest de caja negra
```

Los tests agregan `src/` al `sys.path` (ver `tests/conftest.py`), por eso los
módulos se importan como `import gestor`, no `from src import gestor`.

## Comandos

```bash
pip install -r requirements.txt   # pytest y ruff
pytest                            # suite completa (debe pasar al 100 %)
pytest tests/test_gestor.py -k vip   # un subconjunto
ruff check src                    # linter (resultado esperado: 0 errores)
ruff check src --fix              # solo corrige lo trivial (imports, UP009…)
cd src && python main.py          # app interactiva con datos_ejemplo.json
```

## Reglas que NO se negocian

1. **No modificar** ningún archivo existente de `tests/` ni `pyproject.toml`.
   Si un test falla, el que está mal es el cambio, no el test. Sí se permite
   **agregar** archivos de prueba nuevos (p. ej. `tests/test_casos_borde.py`).
2. **No cambiar la API pública que usan los tests**: `agregarProducto`,
   `buscarProducto`, `registrar_venta`, `cotizar`, `actualizar_stock`,
   `eliminar_producto`, `reiniciar_sistema`, `INVENTARIO`, `VENTAS`,
   `ultimo_error`, `almacen.guardar_datos/cargar_datos`,
   `reportes.productos_stock_bajo/total_vendido/mas_vendidos/reporte_inventario`.
   `agregarProducto` y `buscarProducto` conservan su camelCase (están en
   `ignore-names` del linter).
3. **Comportamiento idéntico**: mismos montos (redondeo a 2 decimales en los
   mismos puntos), mismos mensajes de `ultimo_error`, mismo orden de
   validaciones, mismo texto del ticket y de los reportes, mismo formato JSON.
4. `INVENTARIO` y `VENTAS` se **mutan en sitio** (`clear()`, `update()`,
   `append()`); nunca reasignarlos, porque otros módulos y los tests guardan
   la referencia al objeto.
5. **Una refactorización a la vez.** Después de cada una: `pytest` y
   `ruff check src`. No se avanza con tests en rojo.

## Convenciones de código

- PEP 8, líneas ≤ 88 caracteres, `snake_case` para funciones y variables,
  `MAYUSCULAS` para constantes de módulo.
- Nombres en **español** y descriptivos (`subtotal`, `producto`, `descuento`),
  nunca `aux`, `temp2`, `x`, `t`, `hacer_cosa`.
- Sin números mágicos: tasas, umbrales y prefijos van en constantes
  con nombre al inicio del módulo (`TASA_IVA`, `STOCK_MINIMO`…).
- Type hints en todas las funciones (sintaxis 3.10: `str | None`,
  `list[Producto]`). Los registros se describen con `TypedDict`.
- Docstring de una línea (o breve) en cada función pública; comentarios solo
  para explicar el *porqué*, no el *qué*.
- Validaciones con **cláusulas de guarda** (retorno temprano), no `if`
  anidados. Funciones con complejidad ciclomática ≤ 10.
- Archivos siempre con `with open(..., encoding="utf-8")`. Capturar
  excepciones **específicas** (`json.JSONDecodeError`, `KeyError`, `OSError`),
  nunca `except Exception` a secas.
- Sin código muerto ni código comentado: para eso está el historial de git.

### Ejemplo del estilo esperado

```python
# Mal (estilo original)
if codigo is not None and codigo != "":
    if codigo in INVENTARIO:
        ...

# Bien
def _registrar_error(mensaje: str) -> None:
    global ultimo_error
    ultimo_error = mensaje

if not codigo:
    _registrar_error("codigo vacio")
    return None
```

## Cómo quiero que trabajes

- Antes de editar, explica en 3-5 líneas **qué** vas a cambiar y **por qué**.
- Cambios pequeños y enfocados; no mezcles renombrados con cambios de lógica.
- Si una refactorización cambiaría un resultado observable (aunque sea para
  "arreglar" algo), **detente y pregunta** antes de aplicarla.
- Un commit por refactorización, con mensaje convencional en español
  (`refactor: …`, `docs: …`, `test: …`).
- Registra cada paso en `docs/bitacora.md` (prompt, cambio, justificación,
  resultado de tests).
