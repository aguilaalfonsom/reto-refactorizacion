# Reflexión final

> Borrador para personalizar: ajusta el tono y agrega tu experiencia propia.

**¿Qué tan útil fue la IA para detectar y corregir los problemas?**
Muy útil para el diagnóstico inicial: en una sola pasada clasificó los 20
errores de ruff por *code smell* y propuso un orden de menor a mayor riesgo
(primero borrar código muerto y nombrar constantes; al final tocar el menú y
los tipos). Ese orden fue clave: cada paso dejaba el código más fácil de leer
para el siguiente.

**¿Qué propuso que yo no había notado?**
Tres cosas. (1) Que `cargar_datos` vaciaba el inventario *antes* de descubrir
que el JSON estaba incompleto, perdiendo los datos en memoria: un bug real que
ninguna prueba cubría. (2) Escribir **pruebas de caracterización antes de
refactorizar**, fijando el texto exacto del ticket y los mensajes de error; la
suite original no los revisaba y eran justo lo más fácil de romper. (3) Validar
el menú con una prueba de extremo a extremo (misma entrada, `diff` de la salida)
en lugar de "confiar" en que el texto no cambió.

**¿Cuándo tuve que corregir o rechazar sus sugerencias?**
- Propuso `Counter.most_common(n)`; al pedirle que comprobara la equivalencia
  resultó distinta con `n` negativo, así que la rechacé.
- Usó la sintaxis genérica `def f[T]()`, que solo existe en Python 3.12, cuando
  el proyecto apunta a 3.10.
- Al poner type hints cambió `0` por `0.0` y el reporte vacío pasó de `$0` a
  `$0.0`. Lo atrapó una prueba nueva, no la revisión a ojo.

**¿Qué aprendí?**
- La IA optimiza lo que le pides: si el prompt no dice "comportamiento
  idéntico, mismo redondeo, mismo texto", puede "mejorar" cosas que no debía.
  Los mejores prompts fueron los que incluían **restricciones explícitas y una
  forma de verificarlas** ("compruébalo con `diff`", "demuéstrame con `grep`
  que no se usa", "escribe primero la prueba que falle").
- `CLAUDE.md` funciona como un contrato: escribir ahí las reglas (no tocar
  tests, mutar en sitio, API pública) evitó repetirlas en cada prompt.
- Un cambio por commit hace que, cuando algo falla, sepas exactamente qué lo
  rompió.
- La responsabilidad sigue siendo mía: dos de los tres errores de la IA no
  rompían la suite original; solo los detectaron las pruebas que agregamos.
  **La IA acelera mucho, pero las pruebas son las que dan la confianza.**
