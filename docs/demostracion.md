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
3. Tener abiertas:
   - una ventana normal del navegador en <http://127.0.0.1:8010>;
   - una **ventana privada** (Ctrl + Shift + N) para entrar como otro usuario;
   - **DBeaver** con la conexión a `data/labtrack.db` ya creada (ver abajo) y el archivo [consultas-demo.sql](consultas-demo.sql) abierto;
   - una segunda terminal en la carpeta del proyecto para las pruebas.
4. Contraseña de las cuentas de prueba: valor de `DEMO_PASSWORD` en `.env`.
5. Revisar que no haya proyectos de prueba con texto al azar: aparecerían en las consultas de la base de datos.

## Recorrido

| Tiempo | Qué se muestra | Qué se dice |
|---|---|---|
| 0:00 | Pantalla de acceso (V2) | Problema: experimentos repartidos entre notebooks y notas; LabTrack los reúne en una bitácora. No hay registro público: las cuentas las crea el administrador. |
| 0:40 | Entrar como `ana@example.com`; abrir **Detección de fraude** | Tarjetas con mejor métrica, gráfica de evolución (AUC, mayor es mejor), último récord. |
| 1:30 | **+ Experimento** con F12 → Network abierto: `XGBoost`, `transacciones-v4`, `AUC`, `0.93`, estado **Planeado**; Guardar | Recorrido: `app.js` → `POST /api/projects/{id}/experiments` con cookie y token CSRF → FastAPI valida sesión, CSRF y campos → SQLAlchemy guarda → 201. La gráfica y el récord se actualizan. |
| 2:40 | En **DBeaver**, consulta 5 | El experimento que se acaba de guardar ya está en la tabla `experiments`, con su `status`. |
| 3:10 | Filtrar por `XGBoost`, luego por un modelo inexistente, limpiar | Filtro exacto por modelo. |
| 3:30 | **Eliminar** el proyecto → confirmar | La API responde 409: un proyecto con experimentos no se puede borrar (regla de negocio). |
| 3:50 | Ventana privada: entrar como `luis@example.com` | Luis no ve nada de Ana. Autenticación (quién eres) frente a autorización (qué puedes tocar): los IDs ajenos responden 404. |
| 4:30 | En la segunda terminal: `python -m pytest tests/test_domain.py -k tenant -v` | La prueba intenta las 8 operaciones sobre IDs ajenos y espera 404: `PASSED`. |
| 5:00 | Detener Uvicorn (Ctrl + C), arrancarlo otra vez, recargar | Persistencia: los datos están en `data/labtrack.db`, no en memoria. |
| 5:30 | **DBeaver**: consultas 1, 2, 3, 6 y 7; diagrama ER | Tablas y relaciones; contraseñas como hash Argon2; regla `ON DELETE RESTRICT`; migración `0002` y columna `status`. |
| 6:40 | Entrar como `admin@example.com` → **Usuarios** | Solo el administrador crea cuentas (`ADMIN_EMAILS`); ve conteos, no los proyectos de nadie. |
| 7:10 | Botón **V2 · Cambiar a V1** | La interfaz original del taller se conserva como respaldo, sobre la misma API y sin cerrar sesión. |
| 7:30 | Cierre | Documentación: README, arquitectura, evidencias, ejercicio 4, diagnóstico y mejoras propias. CI con 84 pruebas en verde. |

Reparto sugerido: **Diego** acceso, panel, V2/V1 y administrador; **César** experimento nuevo con estado, migración y DBeaver; **Irving** recorrido de la petición, aislamiento, pruebas y persistencia.

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
| 4. Experimentos de un proyecto | Consulta con `JOIN` a proyecto y dueño |
| 5. Últimos experimentos | Persistencia en vivo: lo guardado en la app aparece aquí |
| 6. Llave foránea de `experiments` | `ON DELETE RESTRICT`: origen del 409 al borrar |
| 7. Migración y columnas | `alembic_version = 0002` y la columna `status` con valor por defecto |
| 8. Experimentos por estado | Datos del ejercicio 4 |
| 9. Sesiones | Se guarda el hash del token de sesión, nunca el token |

No mostrar la columna `csrf_token` de `auth_sessions` ni el archivo `.env`.
