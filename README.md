# LabTrack

Bitácora web de **proyectos y experimentos** de laboratorio. Cada persona inicia sesión, registra sus proyectos y, dentro de cada uno, los experimentos con modelo, versión del dataset, métrica, valor, estado y notas. Cada usuario solo ve y modifica sus propios datos.

Proyecto basado en el taller *Del prompt al despliegue: desarrollo de software con agentes de IA* (ruta básica: Python + SQLite).

## Tecnologías

- **Frontend:** HTML, CSS y JavaScript, servido por la misma aplicación.
- **API:** FastAPI con validación Pydantic.
- **Persistencia:** SQLAlchemy y SQLite (`data/labtrack.db`), con migraciones Alembic.
- **Seguridad:** contraseñas Argon2, sesión en cookie HttpOnly guardada en la BD, token CSRF y validación de origen.

## Requisitos

- Python **3.11 o superior** (recomendado 3.12).
- Git.

## Instalación

Desde una terminal, en la carpeta del proyecto.

**Windows (Git Bash):**

```bash
python -m venv .venv
source .venv/Scripts/activate
```

**Windows (PowerShell):**

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
```

**macOS / Linux:**

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Después, con el entorno activado:

```bash
python -m pip install -r requirements-dev.txt
python scripts/init_env.py
python -m alembic upgrade head
python -m app.cli seed-demo
```

- `init_env.py` crea `.env` con claves aleatorias y `ADMIN_EMAILS` (correos con permiso de administrador). Nunca reemplaza uno existente y **no se sube a GitHub**.
- `alembic upgrade head` crea o actualiza las tablas.
- `seed-demo` crea dos usuarios de prueba con datos ficticios.

## Arranque

```bash
python -m uvicorn app.main:create_app --factory --reload --host 127.0.0.1 --port 8010
```

Abre <http://127.0.0.1:8010>.

| Usuario | Contraseña |
|---|---|
| `ana@example.com` | valor de `DEMO_PASSWORD` en tu `.env` |
| `luis@example.com` | valor de `DEMO_PASSWORD` en tu `.env` |

### Administrador

No hay registro público: las cuentas las crea el administrador. Para preparar la cuenta de administrador local:

```bash
python -m app.cli seed-admin
```

Entra con `admin@example.com` y la misma `DEMO_PASSWORD`. El botón **Usuarios** (solo visible para el administrador) permite crear cuentas y ver la lista. El administrador no puede ver los proyectos de los demás; solo cuántos tiene cada uno. Los correos con este permiso se definen en `ADMIN_EMAILS` dentro del `.env`.

Para llenar la app con datos de muestra (4 usuarios, 15 proyectos y más de 100 experimentos ficticios):

```bash
python -m app.cli seed-showcase
```

La documentación interactiva de la API está en <http://127.0.0.1:8010/docs>.

## Versiones de la interfaz

- **V2** (<http://127.0.0.1:8010/>): diseño propio del equipo, con gráfica de evolución, indicadores y panel de usuarios del administrador.
- **V1** (<http://127.0.0.1:8010/v1>): interfaz original de la plantilla del taller, conservada como respaldo.

Ambas usan la misma API y la misma base de datos; el botón de la esquina inferior izquierda cambia de una a otra sin cerrar la sesión.

## Pruebas

```bash
python -m pytest -q
python -m ruff check .
```

Las pruebas usan bases temporales y no tocan `data/labtrack.db`. Cubren autenticación, CRUD, aislamiento entre usuarios, validación, persistencia, migraciones, permisos del administrador, indicadores y las dos versiones de la interfaz.

## Documentación

- [Arquitectura, ERD y qué pasa al pulsar Guardar](docs/arquitectura-equipo.md)
- [Evidencias de los ejercicios 1 a 3](docs/evidencias.md)
- [Ejercicio 4: estado de los experimentos](docs/mejora-status.md)
- [Mejoras propias del equipo](docs/mejoras-propias.md)
- [Diagnóstico y correcciones](docs/diagnostico.md)
- [Guion de demostración y consultas de la base de datos](docs/demostracion.md)
- [Contrato de la API](docs/02-arquitectura.md)

## Limitaciones

- Ejecución local en `127.0.0.1`; no está publicado en internet.
- No hay recuperación de contraseña: si alguien la olvida, el administrador debe crearle una cuenta nueva.
- Solo hay dos roles: usuario y administrador (por `ADMIN_EMAILS`); no hay colaboración entre usuarios en un mismo proyecto.
- La ruta avanzada (Docker Compose + PostgreSQL) no forma parte de esta entrega.
