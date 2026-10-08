# Reto: Refactorización Asistida por IA

## Gestor de inventario y ventas — Tienda "La Esquina"

Este repositorio contiene una aplicación de consola en Python para administrar
el inventario y las ventas de una tienda pequeña: alta de productos, registro
de ventas con descuentos e IVA, cotizaciones, alertas de stock bajo, reporte de
más vendidos y persistencia de datos en JSON.

**El programa funciona correctamente** (todas las pruebas pasan), pero el código
fue escrito "al aventón" y arrastra una cantidad importante de malas prácticas:
funciones gigantes que hacen de todo, lógica duplicada, nombres crípticos,
números mágicos, estado global, código muerto, anidamiento excesivo, estilos de
nombrado mezclados... Tu misión es **mejorarlo sin romperlo**, usando Claude
Code como asistente.

> **Estado:** refactorizado en la rama `refactorizacion`. 45 pruebas en verde,
> `ruff check src` sin errores y `mypy --strict` sin errores. Detalle de cada
> paso en [`docs/bitacora.md`](docs/bitacora.md). Entrega: Pull Request
> [#1](https://github.com/aguilaalfonsom/reto-refactorizacion/pull/1) (`refactorizacion` → `main`).

### Estructura del proyecto

```
.
├── CLAUDE.md            # Instrucciones para Claude Code (convenciones y reglas)
├── .claudeignore        # Archivos que Claude Code no debe leer
├── src/
│   ├── gestor.py        # Reglas de negocio: productos, ventas, cotizaciones
│   ├── almacen.py       # Carga y guardado de datos (JSON)
│   ├── reportes.py      # Reportes e indicadores
│   └── main.py          # Menú interactivo de consola
├── tests/               # Suite pytest original + test_casos_borde.py (nuevo)
├── docs/
│   ├── bitacora.md      # Registro de cada refactorización (prompts, cambios)
│   ├── reflexion.md     # Aprendizajes y conclusiones
│   └── evidencia/       # Salida de pytest/ruff después de cada paso
├── scripts/
│   └── entrada_e2e.txt  # Entrada para la prueba de extremo a extremo del menú
├── datos_ejemplo.json   # Datos de ejemplo para el menú interactivo
├── requirements.txt
├── pyproject.toml       # Configuración del linter (ruff)
└── BITACORA_TEMPLATE.md # Plantilla original de la bitácora
```

## Instalación y ejecución

**Requisitos previos:** Python 3.10 o superior, `git` y `pip`.
Dependencias (en `requirements.txt`): `pytest>=8.0`, `ruff>=0.6`.

```bash
# 1. Clonar el repositorio y cambiar a la rama del reto
git clone https://github.com/aguilaalfonsom/reto-refactorizacion.git
cd reto-refactorizacion
git checkout refactorizacion

# 2. Crear y activar un entorno virtual
python -m venv .venv
source .venv/bin/activate        # En Windows: .venv\Scripts\activate

# 3. Instalar dependencias
pip install -r requirements.txt

# 4. Ejecutar la suite de pruebas (45 passed)
pytest

# 5. Ejecutar el linter (All checks passed!)
ruff check src

# 6. (Opcional) Probar la aplicación interactiva
cd src && python main.py
```

## Instrucciones del reto

Trabaja en un **fork** de este repositorio y sigue estos pasos:

1. **Configura el proyecto para Claude Code.** Crea un `CLAUDE.md` con el
   contexto del proyecto (qué hace, cómo correr las pruebas, reglas que la IA
   debe respetar — por ejemplo, *no modificar los tests*) y un `.claudeignore`
   con lo que no debe leer (entornos virtuales, cachés, datos generados).
   Crear estos archivos es parte del reto: **no vienen incluidos**.
2. **Explora el código con Claude Code.** Pídele un diagnóstico: qué *code
   smells* detecta y qué refactorizaciones recomienda. Prioriza.
3. **Aplica al menos 5 refactorizaciones significativas**, una a la vez.
   Ejemplos válidos: dividir una función gigante, extraer lógica duplicada,
   renombrar con nombres descriptivos y estilo consistente, reemplazar números
   mágicos por constantes, aplanar condicionales anidados, eliminar código
   muerto, agregar type hints, reducir el estado global, separar lógica de
   entrada/salida. Cambios cosméticos aislados (una línea, un espacio) no
   cuentan como refactorización significativa.
4. **Valida con `pytest` y `ruff check src` después de CADA refactorización.** La suite de
   pruebas es de caja negra: si un cambio la rompe, tu refactorización alteró
   el comportamiento y debes corregirla. **No está permitido modificar los
   tests** para hacerlos pasar.
5. **Documenta cada prompt en la bitácora.** Copia `BITACORA_TEMPLATE.md` a
   `BITACORA.md` y llena una fila por refactorización: prompt usado, cambio
   realizado, justificación y resultado de los tests. Cierra con tu reflexión.
6. **Entrega mediante Pull Request** hacia tu propio repositorio (rama
   `refactorizacion` → `main`), con commits atómicos (idealmente uno por
   refactorización) y la bitácora incluida. Comparte la liga del PR en la
   plataforma del curso.

## Criterios de evaluación

| Criterio | Descripción | Peso |
|----------|-------------|------|
| Configuración | `CLAUDE.md` y `.claudeignore` completos y pertinentes | 15% |
| Calidad de refactorizaciones | ≥5 refactorizaciones significativas, bien elegidas y bien ejecutadas | 30% |
| Tests pasando | La suite completa pasa al final (y después de cada cambio) | 20% |
| Bitácora | Prompts documentados, cambios explicados y justificados | 25% |
| Reflexión | Análisis crítico del trabajo con la IA | 10% |

## Reglas

- No modifiques los archivos de `tests/` ni `pyproject.toml`.
- El código final de `src/` debe pasar `ruff check src` **sin errores**. La
  configuración ya viene incluida en `pyproject.toml`; cada regla corresponde a
  un *code smell* real del proyecto (funciones demasiado complejas, nombres que
  no siguen PEP 8, archivos abiertos sin `with`, imports sin usar, `if`
  anidados…). `ruff check src --fix` corrige solo los triviales: el resto es
  trabajo de refactorización. Las funciones `agregarProducto` y
  `buscarProducto` conservan su nombre porque los tests las usan.
- El comportamiento observable del programa debe mantenerse idéntico.
- Puedes (y debes) usar Claude Code, pero **tú eres responsable** de revisar,
  entender y validar cada cambio que la IA proponga.
