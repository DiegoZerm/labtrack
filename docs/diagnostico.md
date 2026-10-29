# Diagnóstico y correcciones

Fallos reales encontrados durante el desarrollo, documentados con el mismo método del ejercicio 5: **síntoma → reproducción → observación → corrección mínima → comprobación**.

## 1. Editar un experimento borraba campos que no se enviaban

### Síntoma

Al editar un experimento desde la **V1** (`/v1`, la interfaz original del taller), las observaciones se perdían. Con el campo `status` del ejercicio 4 el efecto habría sido peor: un experimento *Planeado* editado desde la V1 regresaba a *Completado* sin que nadie lo pidiera.

### Reproducción

Se creó un experimento con notas y se editó con `PUT /api/experiments/{id}` **sin** enviar `notes`, igual que hace el formulario de la V1. Script contra el código anterior a la corrección (commit `4190062`):

```text
antes de editar : Resultado de ejemplo
PUT sin notes   : 200 | notes guardadas: '' | metric_value: 0.87
```

La API respondió **200** y guardó el nuevo valor de la métrica, pero las notas quedaron vacías. No había error en el log: el fallo era silencioso.

### Observación

En `app/routes/experiments.py`, la ruta copiaba al registro **todos** los campos del esquema:

```python
for field, value in payload.model_dump().items():
```

`ExperimentInput` define valores por defecto (`notes=""` y, con el ejercicio 4, `status="completed"`). Cuando un campo no llega en el JSON, Pydantic lo rellena con su valor por defecto y `model_dump()` lo incluye, así que se sobrescribía el dato guardado.

### Corrección mínima

Copiar solo los campos que el cliente envió de verdad (commit `f6ec3b8`, PR #5):

```python
for field, value in payload.model_dump(exclude_unset=True).items():
```

Los campos obligatorios (nombre, modelo, dataset, métrica y valor) siguen exigiéndose y validándose igual; solo cambia que un campo opcional ausente ya no se reemplaza por su valor por defecto.

### Comprobación

Mismo script contra el código corregido:

```text
antes de editar : Resultado de ejemplo
PUT sin notes   : 200 | notes guardadas: 'Resultado de ejemplo' | metric_value: 0.87
```

- Prueba nueva `test_editing_without_optional_fields_keeps_them` en `tests/test_versiones.py`.
- La prueba del ejercicio 4 (`test_experiment_status`) también verifica que editar sin `status` conserva el estado.
- Suite completa: `python -m pytest -q` pasa; la CI la ejecuta con SQLite y PostgreSQL en Python 3.11 y 3.12.

## 2. Las tarjetas de proyecto mostraban datos viejos

- **Síntoma:** después de crear un experimento, su tarjeta seguía diciendo "Sin experimentos todavía"; después de editar un valor de 0.84 a 0.87, la tarjeta seguía mostrando ★ 0.84. El resumen "Último récord" sí se actualizaba.
- **Reproducción:** crear un experimento en un proyecto vacío y observar la tarjeta del proyecto en la columna izquierda.
- **Observación:** en `frontend/panel.js`, `decorarTarjetas()` saltaba cualquier tarjeta que ya tuviera su línea de datos (`if (... tarjeta.querySelector(".tarjeta-datos")) return;`), así que al refrescar nunca la reemplazaba.
- **Corrección mínima (PR #7):** quitar la línea anterior antes de dibujar la nueva (`tarjeta.querySelector(".tarjeta-datos")?.remove()`).
- **Comprobación:** en el navegador, crear → "1 exp. ★ 0.84 F1"; editar a 0.87 → "★ 0.87 F1".

## 3. La integración continua fallaba antes de ejecutar las pruebas

- **Síntoma:** el workflow de GitHub Actions terminaba en rojo en todos los PRs, en el paso *Initialize containers*.
- **Observación del log:** `unknown shorthand flag: 'U' in -U` y `Exit code 125` al ejecutar `docker create` del servicio PostgreSQL.
- **Causa:** el runner no respetaba las comillas simples de `--health-cmd 'pg_isready -U labtrack_test -d labtrack_test'` y pasaba `-U` como opción de `docker create`.
- **Corrección mínima (PR #2):** `--health-cmd pg_isready`, que comprueba que el servidor acepte conexiones.
- **Comprobación:** la CI llega a las pruebas y pasa en Python 3.11 y 3.12 contra SQLite y PostgreSQL.
