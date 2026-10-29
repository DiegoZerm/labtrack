# Guion de demostración (6–8 minutos)

Recorrido para presentar LabTrack: la aplicación funcionando, la petición que viaja del navegador a la API, la base de datos y las pruebas.

## Preparación (antes de presentar)

1. Base de datos al día y con datos de muestra:
   ```bash
   python -m alembic upgrade head
   python -m app.cli seed-demo
   python -m app.cli seed-admin
   python -m app.cli seed-showcase
   ```
2. Arrancar la app y dejar la terminal visible:
   ```bash
   python -m uvicorn app.main:create_app --factory --reload --host 127.0.0.1 --port 8010
   ```
3. Cuentas del equipo con sus proyectos. Entrando como `admin@example.com` → **Usuarios**, crear `diego@example.com` y `cesar@example.com` (contraseña: `DEMO_PASSWORD`). Después, cada uno registra sus proyectos:
   - **Diego** · *GreenSense · humedad del sustrato* (RMSE): Línea base 8.4, Ventanas de 1 h 6.1, Variables de riego 4.5 (Completados), Historial de 24 h 5.3 (**Descartado**) y Ajuste de hiperparámetros 4.2 (**Planeado**, meta). *HPC · multiplicación de matrices* (Speedup): Secuencial 1.0, OpenMP 4 hilos 3.4, OpenMP 8 hilos 5.1 y Bloques de caché 6.8 (**Planeado**).
   - **César** · *IoT · distancia con HC-SR04* (MAE en cm) y *Clasificación de residuos* (F1).
4. Tener abiertas:
   - una ventana normal del navegador en <http://127.0.0.1:8010>;
   - una **ventana privada** (Ctrl + Shift + N) para entrar como otro usuario;
   - **DBeaver** con la conexión a `data/labtrack.db` ya creada (ver abajo) y el archivo [consultas-demo.sql](consultas-demo.sql) abierto;
   - una segunda terminal en la carpeta del proyecto para las pruebas.
5. Contraseña de las cuentas: valor de `DEMO_PASSWORD` en `.env`.
6. Revisar que no haya proyectos de prueba con texto al azar: aparecerían en las consultas de la base de datos.

## Recorrido

| Tiempo | Qué se muestra | Qué se dice |
|---|---|---|
| 0:00 | Pantalla de acceso (V2) | Problema: experimentos repartidos entre notebooks y notas; LabTrack los reúne en una bitácora. No hay registro público: las cuentas las crea el administrador. |
| 0:40 | Entrar como `diego@example.com`; abrir **GreenSense · humedad del sustrato** | Tarjetas con mejor métrica, gráfica de evolución (RMSE, **menor es mejor**) y último récord. La tabla muestra los tres estados: la **meta planeada** (4.2) no entra a la gráfica ni compite por el mejor, porque todavía no es un resultado. |
| 1:30 | F12 → Network abierto. **Editar** «Ajuste de hiperparámetros»: valor `4.1`, estado **Completado**; Guardar | La meta se cumplió. Recorrido: `app.js` → `PUT /api/experiments/{id}` con cookie y token CSRF → FastAPI valida sesión, CSRF y campos (un estado desconocido daría 422) → SQLAlchemy guarda → 200. La gráfica gana un punto y la tarjeta pasa a ★ 4.1 RMSE. |
| 2:40 | En **DBeaver**, consulta 4 (F5 para refrescar) | El cambio ya está en la tabla `experiments`, con su `status` en `completed`. |
| 3:10 | Filtrar por `XGBoost`, luego por un modelo inexistente, limpiar | Filtro exacto por modelo. |
| 3:30 | **Eliminar** el proyecto → confirmar | La API responde 409: un proyecto con experimentos no se puede borrar (regla de negocio). |
| 3:50 | Ventana privada: entrar como `cesar@example.com` | César solo ve sus proyectos (IoT y residuos); nada de Diego. Autenticación (quién eres) frente a autorización (qué puedes tocar): los IDs ajenos responden 404. |
| 4:30 | En la segunda terminal: `python -m pytest tests/test_domain.py -k tenant -v` | La prueba intenta las 8 operaciones sobre IDs ajenos y espera 404: `PASSED`. |
| 5:00 | Detener Uvicorn (Ctrl + C), arrancarlo otra vez, recargar | Persistencia: los datos están en `data/labtrack.db`, no en memoria. |
| 5:30 | **DBeaver**: consultas 1, 2, 3, 6 y 7; diagrama ER | Tablas y relaciones; contraseñas como hash Argon2; regla `ON DELETE RESTRICT`; migración `0002` y columna `status`. |
| 6:40 | Entrar como `admin@example.com` → **Usuarios** | Solo el administrador crea cuentas (`ADMIN_EMAILS`); aparecen las de Diego y César con sus conteos, pero el administrador no puede abrir sus proyectos. |
| 7:10 | Botón **V2 · Cambiar a V1** | La interfaz original del taller se conserva como respaldo, sobre la misma API y sin cerrar sesión. |
| 7:30 | Cierre | Documentación: README, arquitectura, evidencias, ejercicio 4, diagnóstico y mejoras propias. CI con todas las pruebas en verde. |

Reparto sugerido: **Diego** acceso, GreenSense, edición con estado, V2/V1 y administrador; **César** su cuenta en la ventana privada, filtro, regla de borrado y DBeaver; **Irving** recorrido de la petición en Network, aislamiento, pruebas y persistencia.

Si se ensaya la demo, devolver después «Ajuste de hiperparámetros» a **Planeado** con valor 4.2 para presentarla igual.

## DBeaver: conectar la base de datos

1. **Database → New Database Connection → SQLite → Next**.
2. En **Path**, elegir el archivo `data/labtrack.db` de la carpeta del proyecto.
3. La primera vez, DBeaver ofrece descargar el controlador de SQLite: **Download**.
4. Opcional y recomendado para presentar: **Edit Connection → General → Read-only connection**, para no modificar datos por accidente mientras la app está corriendo.
5. **Finish**. En el panel izquierdo aparecen las tablas en **Schemas → main → Tables**.

Para el **diagrama ER**: clic derecho sobre la conexión (o sobre *Tables*) → **View Diagram**. Muestra `users → projects → experiments` y las tablas de soporte `auth_sessions`, `login_throttles` y `alembic_version`.

Para las consultas:

1. Conectar primero: doble clic en la conexión en **Database Navigator** (aparece una palomita verde).
2. **File → Open File…** → `docs/consultas-demo.sql`.
3. Asignar la conexión al editor con **Ctrl + 9** (o el selector **N/A** de la barra del editor) → elegir la conexión. Sin este paso DBeaver responde *No active connection*.
4. Colocar el cursor en una consulta y presionar **Ctrl + Enter**.

Alternativa: clic derecho en la conexión → **SQL Editor → Open SQL script** (Ctrl + ]) abre un editor ya conectado; ahí se pegan las consultas. Después de guardar algo en la app, presionar **F5** en el resultado para refrescarlo.

| Consulta | Qué demuestra |
|---|---|
| 1. Tablas | Estructura de la base de datos |
| 2. Usuarios con sus conteos | Relación usuario → proyecto → experimento |
| 3. Hash de contraseñas | Se guarda un hash Argon2, nunca la contraseña |
| 4. Experimentos de GreenSense | Consulta con `JOIN` a proyecto y dueño; muestra los tres estados |
| 5. Últimos experimentos | Persistencia en vivo: lo guardado en la app aparece aquí |
| 6. Llave foránea de `experiments` | `ON DELETE RESTRICT`: origen del 409 al borrar |
| 7. Migración y columnas | `alembic_version = 0002` y la columna `status` con valor por defecto |
| 8. Experimentos por estado | Datos del ejercicio 4 |
| 9. Sesiones | Se guarda el hash del token de sesión, nunca el token |

No mostrar la columna `csrf_token` de `auth_sessions` ni el archivo `.env`.
