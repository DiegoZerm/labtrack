# Mejoras propias

El campo `status` de los experimentos corresponde al **ejercicio 4** del taller y está documentado en [mejora-status.md](mejora-status.md). Lo que sigue son mejoras que el equipo agregó por su cuenta sobre la solución básica.

## 1. Panel de indicadores y gráfica de evolución

**Problema.** Con varios experimentos por proyecto, la tabla no responde preguntas simples: ¿cuál fue el mejor resultado?, ¿está mejorando el modelo?, ¿cuándo fue la última prueba?

**Qué se hizo.**

- `GET /api/insights` (`app/routes/insights.py`) calcula, **solo con datos del usuario de la sesión**, el mejor experimento de cada proyecto, cuántos tiene y su última actividad, además del último récord del usuario.
- El "mejor" respeta la dirección de la métrica: en F1, AUC, Accuracy o R² gana el valor **mayor**; en RMSE, MAE, MSE o MAPE, el **menor**. Cada proyecto se evalúa con su métrica más usada, para no comparar valores de métricas diferentes como si fueran equivalentes (una advertencia de la propia guía del taller).
- `frontend/panel.js` muestra:
  - una **gráfica SVG** de la evolución de la métrica del proyecto, con el mejor punto marcado (se dibuja sin librerías externas, porque la política de seguridad de contenido de la app no permite cargar scripts de otros dominios);
  - **tarjetas de proyecto** con número de experimentos, mejor métrica y última actividad;
  - el **último récord** en el resumen, con un botón para abrir su proyecto.

**Pruebas.** `tests/test_insights.py`: dirección de la métrica, aislamiento entre usuarios y sesión obligatoria.

## 2. Gestión de usuarios por el administrador

**Problema.** El taller indica que las cuentas las crea el administrador con una herramienta local (`python -m app.cli create-user`) y deja el registro público fuera del alcance. Eso obliga a abrir una terminal en el servidor cada vez que llega una persona nueva.

**Qué se hizo.**

- Los correos con permiso de administrador se definen en `ADMIN_EMAILS` dentro del `.env`; no requiere cambiar la base de datos.
- `GET /api/admin/users` y `POST /api/admin/users` (`app/routes/admin.py`) están protegidos con `require_admin`: un usuario normal recibe **403**.
- En la interfaz, solo el administrador ve el botón **Usuarios**: crea cuentas (con opción de generar una contraseña segura) y ve la lista con cuántos proyectos y experimentos tiene cada persona.
- El administrador **no** puede abrir los proyectos de los demás ni ver ningún hash de contraseña: la privacidad de cada usuario se mantiene.
- `python -m app.cli seed-admin` crea la cuenta local `admin@example.com`.

**Pruebas.** `tests/test_admin.py`: 8 pruebas (rol en la sesión, crear y entrar, listado sin secretos, duplicados e inválidos, 403 para usuarios normales, sesión y CSRF obligatorios, sin registro público, sin administradores por defecto).

## 3. Interfaz V2 con la V1 como respaldo

**Problema.** Cambiar la interfaz completa es arriesgado a días de la entrega: si algo falla en la nueva, no debe perderse la que ya funcionaba.

**Qué se hizo.**

- **V2** (`/`): diseño propio con paleta azul hielo, lila, rosa y champán, tipografías Inter y Cormorant Garamond servidas desde el propio proyecto (la política de seguridad bloquea fuentes externas), acceso en tarjeta de cristal y ventanas de confirmación propias en lugar de `confirm()`.
- **V1** (`/v1`): copia sin cambios de lógica de la interfaz original del taller, con la misma API, la misma base de datos y la misma política de seguridad.
- Un botón en la esquina inferior izquierda cambia de una versión a otra **sin cerrar la sesión**.
- La API conserva los campos opcionales que no llegan al editar, para que la V1 (que no conoce `status`) no altere datos creados en la V2. Ver [diagnostico.md](diagnostico.md#1-editar-un-experimento-borraba-campos-que-no-se-enviaban).

**Pruebas.** `tests/test_versiones.py`: ambas versiones se sirven con su política de seguridad, se enlazan entre sí, la V1 conserva su acceso original y editar sin campos opcionales no los borra.

## 4. Datos de muestra

`python -m app.cli seed-showcase` crea 4 usuarios, 15 proyectos y 116 experimentos ficticios (clasificación, regresión y otros casos) con métricas que mejoran por iteración y fechas repartidas en dos meses. Sirve para demostrar la app con contenido realista. Es idempotente: ejecutarlo dos veces no duplica datos. No modifica `seed-demo`, que es el que usan las pruebas y las guías del taller.

**Pruebas.** `tests/test_showcase.py`: idempotencia y que cada usuario solo vea sus proyectos.
