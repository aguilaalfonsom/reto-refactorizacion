# Bitácora de refactorización

**Nombre:** _(completar)_
**Matrícula:** _(completar)_
**Fecha:** 8 de octubre de 2026
**Rama:** `refactorizacion` → `main`

Cada refactorización se aplicó por separado, en su propio commit, y se validó
con `pytest` y `ruff check src` antes de continuar. La salida completa de cada
validación está en [`docs/evidencia/`](evidencia/).

---

## 0. Punto de partida

| Métrica | Inicio | Final |
|---|---|---|
| Tests | 20 / 20 ✅ | 45 / 45 ✅ (20 originales + 25 nuevos) |
| Errores de `ruff check src` | **20** | **0** |
| `mypy --strict` | no aplicaba (sin type hints) | 0 errores |
| Complejidad máxima (McCabe) | `menu` = 17, `registrar_venta` = 12 | 5 |
| Funciones / comentarios muertos | 3 (`calcular_descuento_viejo`, `reporteViejoCSV`, `exportar_txt` comentado) | 0 |

Evidencia: [`00_estado_inicial.txt`](evidencia/00_estado_inicial.txt).

### Diagnóstico (modo chat)

**Prompt:**

> Lee CLAUDE.md y todos los archivos de `src/`. **No modifiques nada todavía.**
> Hazme un diagnóstico de *code smells*: para cada uno indica archivo, función,
> el smell, qué regla de ruff lo detecta (si aplica) y el riesgo de corregirlo
> (bajo/medio/alto) considerando que los tests son de caja negra. Al final,
> propón un orden de refactorizaciones de menor a mayor riesgo.

**Code smells encontrados:**

| # | Smell | Dónde | Regla ruff |
|---|---|---|---|
| 1 | Función gigante que valida, calcula, descuenta stock, arma ticket y guarda | `gestor.registrar_venta` | C901 (12) |
| 2 | Menú con cadena de 8 `if/elif` mezclando E/S y lógica | `main.menu` | C901 (17) |
| 3 | Lógica de descuentos/IVA **duplicada** (riesgo de que cotización y venta difieran) | `registrar_venta` / `cotizar` | — |
| 4 | Pirámide de `if` anidados (4 niveles en validación, 4 en VIP) | `registrar_venta` | SIM102 ×3, SIM108 |
| 5 | Números mágicos: `0.16`, `0.10`, `0.05`, `0.02`, `1000`, `500`, `200`, `5`, `"VIP"` | `gestor`, `reportes` | — |
| 6 | Nombres crípticos: `aux`, `temp2`, `x`, `t`, `d`, `hacer_cosa` | todos | — |
| 7 | Estilos mezclados: `contadorVentas`, `hayArchivo`, `reporteViejoCSV` | `gestor`, `almacen`, `reportes` | N816, N802 ×2 |
| 8 | Código muerto: función "por si acaso", reporte CSV obsoleto, función comentada, `MODO_DEBUG` sin uso, `import os` sin uso | `gestor`, `reportes` | F401 |
| 9 | Archivos sin `with`, `except Exception` genérico | `almacen`, `reportes` | SIM115 ×3, UP015 |
| 10 | Ordenamiento de burbuja hecho a mano (con un TODO) | `reportes.mas_vendidos` | — |
| 11 | `if cond: return True else: return False` | `almacen.hayArchivo` | SIM103 |
| 12 | Sin type hints; registros como `dict` sin forma documentada | todos | — |
| 13 | Declaraciones `# -*- coding: utf-8 -*-` innecesarias, imports desordenados | todos | UP009 ×4, I001 |

**Hallazgo extra de la IA que yo no había notado:** en `cargar_datos`, si el JSON
es válido pero le falta la clave `"inventario"`, el código **primero vacía el
inventario y después truena con `KeyError`**: se pierde el estado en memoria.
Ningún test original lo cubría.

---

## 1. Configuración y red de seguridad

### 1a. `CLAUDE.md` y `.claudeignore` — commit `2f82eeb`

**Prompt:**

> Crea un CLAUDE.md para este repo. Incluye: qué hace la app y su estructura,
> comandos exactos para tests y linter, reglas no negociables (no tocar
> `tests/` ni `pyproject.toml`, conservar `agregarProducto` y `buscarProducto`,
> comportamiento idéntico), convenciones de estilo con un ejemplo de
> "mal vs bien", y cómo quiero que trabajes (explicar antes de editar, un
> commit por cambio, preguntar si algo cambia un resultado observable).
> Crea también un `.claudeignore` y explica cada exclusión.

**Iteración del CLAUDE.md durante el reto:** las reglas 4 (mutar
`INVENTARIO`/`VENTAS` en sitio) y "sí se permite *agregar* pruebas nuevas" se
redactaron después del diagnóstico, al identificar que eran los dos puntos donde
un refactor podía romper el comportamiento sin que la suite original lo notara.
El historial de commits de `CLAUDE.md` refleja su versión final.

**`.claudeignore`:** excluye entornos virtuales, cachés (`__pycache__`,
`.pytest_cache`, `.ruff_cache`, `.mypy_cache`), datos generados por la app
(`datos_*.json` salvo `datos_ejemplo.json`), logs de evidencia y basura del
SO (`.DS_Store`, `__MACOSX/`). Motivo: no aportan contexto y gastan tokens.

### 1b. Pruebas de caracterización — commit `859f1a5`

**Prompt:**

> Antes de refactorizar, escribe pruebas de caracterización en un archivo
> NUEVO `tests/test_casos_borde.py` (no toques los existentes). Deben fijar el
> comportamiento ACTUAL que la suite no cubre: texto exacto del ticket con y
> sin descuento, todos los mensajes de `ultimo_error` y su orden de validación,
> umbrales exactos de descuento (499/500/999/1000), reglas VIP (prefijo,
> mayúsculas, None, monto mínimo), texto exacto de los reportes, empates en
> `mas_vendidos` y formato del JSON. Ejecútalas contra el código original:
> deben pasar todas.

**Cambio:** 20 pruebas nuevas, todas en verde contra el código **original**.
**Justificación:** la suite original no revisaba el texto del ticket ni los
mensajes de error, que son justo lo que más se toca al refactorizar. Con esto,
cualquier cambio de comportamiento accidental se detecta de inmediato.
**Tests:** 40 / 40 ✅ — [`01_red_de_seguridad.txt`](evidencia/01_red_de_seguridad.txt)

---

## 2. Tabla de refactorizaciones

> Los prompts se transcriben de forma fiel y resumida (la conversación completa
> fue más larga).

| # | Prompt usado | Cambio realizado | Justificación | Tests OK |
|---|---|---|---|---|
| 1 | *"Elimina el código muerto: funciones que nadie llama, código comentado, variables e imports sin uso y las declaraciones `coding: utf-8`. Antes de borrar, demuéstrame con `grep` que no se usan en `src/` ni en `tests/`."* | Se borraron `calcular_descuento_viejo`, `reporteViejoCSV`, la función comentada `exportar_txt`, `MODO_DEBUG`, `import os` en reportes y 4 declaraciones de codificación. Commit `b1d68f3`. | Código que no se ejecuta confunde y hay que mantenerlo; el historial de git ya lo conserva. Ruff: 20 → 13 errores. | ✅ 40/40 |
| 2 | *"Reemplaza todos los números mágicos de `gestor.py` y `reportes.py` por constantes con nombre en MAYÚSCULAS al inicio del módulo, con un comentario que explique la regla de negocio. No cambies ninguna otra línea."* | Constantes `TASA_IVA`, `UMBRAL_/TASA_DESCUENTO_ALTO/MEDIO`, `PREFIJO_CLIENTE_VIP`, `MONTO_MINIMO_VIP`, `TASA_DESCUENTO_VIP`, `NOMBRE_TIENDA`, `FORMATO_FECHA`, `STOCK_MINIMO`. Commit `5bf7250`. | Las reglas de negocio ahora tienen nombre y viven en un solo lugar: cambiar el IVA o el umbral de stock es editar una línea, no buscar `0.16` en todo el código. | ✅ 40/40 |
| 3 | *"`registrar_venta` hace 5 cosas. Divídela en funciones privadas: validación con cláusulas de guarda (mismo orden de validación y mismos mensajes), cálculo de importes, y armado del ticket. Haz que `cotizar` use EXACTAMENTE la misma función de cálculo. Cuida que el redondeo ocurra en los mismos puntos y que el descuento sin rebaja siga siendo `0` (int), no `0.0`."* | Nuevas `_validar_venta`, `_descuento_por_volumen`, `_es_cliente_vip`, `_calcular_importes` (con `NamedTuple Importes`) y `_armar_ticket`. `cotizar` reutiliza `_calcular_importes`. Se eliminaron los 3 `if` anidados del VIP y la pirámide de validación. Commit `0b69842`. | Elimina la duplicación (antes, cambiar un descuento exigía tocar 2 lugares y la cotización podía dejar de coincidir con la venta). Cada función tiene una sola responsabilidad. `registrar_venta` pasa de complejidad 12 a 2. | ✅ 40/40 |
| 4 | *"Renombra variables y funciones con nombres descriptivos en español y snake_case: `contadorVentas`, `hayArchivo`, `hacer_cosa`, y todas las `aux`, `temp2`, `x`, `s`, `t`, `p`, `k`. Actualiza todos los usos. NO renombres `agregarProducto` ni `buscarProducto`. Aprovecha para centralizar el `global ultimo_error` repetido en un helper."* | `contador_ventas`, `hay_archivo`, `formatear_moneda`, `subtotal`, `nuevo_stock`, `producto`, `valor_total`, etc. Helper `_fallar(mensaje, resultado)`. Comprensiones de lista en `buscarProducto` y `productos_stock_bajo`. Commit `746a5be`. | El código se lee como el dominio ("subtotal", "nuevo_stock") en vez de adivinar qué guarda `aux`. Estilo uniforme PEP 8 (N802, N816 resueltos). | ✅ 40/40 |
| 5 | *"Reemplaza el ordenamiento de burbuja de `mas_vendidos` por `sorted()` y el conteo manual por `collections.Counter`. Ojo: en empates debe conservarse el orden de la primera venta, igual que hoy. ¿`Counter.most_common(n)` es equivalente al slicing actual en todos los casos?"* | `Counter` acumula unidades; `sorted(..., reverse=True)` ordena. Commit `2ef4efb`. | Algoritmo O(n²) escrito a mano → función estándar O(n log n), probada y estable. Se cierra el TODO del código. | ✅ 40/40 |
| 6 | *"Mejora el manejo de errores de `almacen.py`: `with open`, excepciones específicas en lugar de `except Exception`, y valida la estructura del JSON ANTES de modificar el estado global. Escribe primero pruebas que demuestren los fallos actuales."* | `_leer_json` valida tipo y claves antes de tocar nada; captura `JSONDecodeError`/`UnicodeDecodeError` (→ "archivo corrupto") y `OSError` (→ "no se pudo leer el archivo"). `guardar_datos` con `with`. Carga en sitio con `clear()` + `update()/extend()`. 4 pruebas nuevas. Commit `f34db4a`. | Corrige un bug real: un JSON incompleto borraba el inventario y luego tronaba. Las 3 pruebas nuevas **fallaban con el código original** ([`07a_bugs_detectados_antes.txt`](evidencia/07a_bugs_detectados_antes.txt)) y pasan ahora. | ✅ 44/44 |
| 7 | *"`menu()` tiene complejidad 17. Separa cada opción en su propia función y reemplaza la cadena de `if/elif` por un diccionario de despacho. La salida en pantalla debe ser idéntica carácter por carácter; compruébalo corriendo el menú original y el nuevo con la misma entrada y haciendo `diff`."* | `OPCIONES: dict[str, (texto, acción)]`, funciones `opcion_*`, `pedir_entero`, `mostrar_error`, `cargar_datos_iniciales`. Imports ordenados. Commit `7f9f99d`. | Separa E/S de la lógica, cada opción se puede leer y probar aislada y agregar una opción es agregar una línea al diccionario. `menu` pasa de 17 a 4. Prueba E2E: **salida y JSON idénticos** ([`08_menu.txt`](evidencia/08_menu.txt)). Ruff: **0 errores**. | ✅ 44/44 |
| 8 | *"Agrega type hints a todas las funciones con sintaxis de Python 3.10 (`str \| None`, `list[...]`). Define `Producto` y `Venta` como `TypedDict`. Debe pasar `mypy --strict`. No cambies ningún valor que se imprima."* | `TypedDict` `Producto` y `Venta`, `NamedTuple Importes`, `TypeVar` en `_fallar`, firmas completas en los 4 módulos. Commit `59cde86`. | Documenta la forma de los datos, el editor autocompleta y mypy detecta errores de tipo antes de ejecutar. `mypy --strict`: 0 errores. | ✅ 45/45 |

---

## 3. Variaciones de prompts e intentos fallidos

Estos son los casos reales en los que la primera propuesta no fue la buena y
cómo se resolvieron.

**Refactorización 5 — `most_common` vs `sorted`.**
La primera sugerencia fue `return Counter(...).most_common(n)` (más corto).
Le pregunté si era equivalente y lo comprobé: con `n` negativo **no** lo es
(`most_common(-1)` → `[]`, el slicing original `[:-1]` → todos menos el último).
**Decisión:** rechacé `most_common` y usé `sorted()` + slicing para conservar
el comportamiento exacto.

**Refactorización 8 — dos errores detectados.**
1. La IA usó la sintaxis `def _fallar[T](...)` (PEP 695), que **solo existe
   en Python 3.12+**; el proyecto apunta a 3.10. Lo cambié por `TypeVar`.
2. Inicializó los acumuladores como `valor_total = 0.0` "para que el tipo
   sea float". Eso cambia el reporte vacío de `$0` a `$0.0`. La prueba nueva
   `test_reportes_vacios_muestran_cero_entero` lo atrapó
   ([`09a_intento_fallido_type_hints.txt`](evidencia/09a_intento_fallido_type_hints.txt));
   la corrección fue `valor_total: float = 0`.

---

## 4. Cómo reproducir la validación

```bash
pytest                      # 45 passed
ruff check src              # All checks passed!
cd src && mypy --strict --python-version 3.10 *.py   # opcional

# Prueba E2E del menú (genera src/datos_ejemplo.json; no lo subas)
cd src && cp ../datos_ejemplo.json . && python main.py < ../scripts/entrada_e2e.txt
```

## Reflexión

Ver [`reflexion.md`](reflexion.md).
