import argparse
from getpass import getpass

from pydantic import EmailStr, TypeAdapter
from sqlalchemy import select

from app.config import Settings
from app.db import make_engine, make_session_factory
from app.models import Experiment, Project, User
from app.security import password_hasher
from app.showcase import seed_showcase


def add_user(db, email, password):
    email = str(TypeAdapter(EmailStr).validate_python(email)).lower()
    if not 12 <= len(password) <= 128:
        raise ValueError("La contraseña debe tener entre 12 y 128 caracteres.")
    if db.scalar(select(User).where(User.email == email)):
        return None
    user = User(email=email, password_hash=password_hasher.hash(password))
    db.add(user)
    db.flush()
    return user


def main():
    parser = argparse.ArgumentParser(description="Administración local de LabTrack")
    parser.add_argument(
        "command", choices=["seed-demo", "seed-showcase", "seed-admin", "create-user"]
    )
    args = parser.parse_args()
    settings = Settings()
    engine = make_engine(settings.database_url)
    try:
        with make_session_factory(engine)() as db:
            if args.command == "create-user":
                email = input("Correo: ").strip()
                password = getpass("Contraseña (12–128 caracteres): ")
                if password != getpass("Repite la contraseña: "):
                    raise ValueError("Las contraseñas no coinciden.")
                user = add_user(db, email, password)
                print("Usuario creado." if user else "El usuario ya existe; no se modificó.")
            elif args.command == "seed-admin":
                if settings.session_cookie_secure:
                    raise ValueError("El seed de demostración solo se permite en el entorno local.")
                if not settings.demo_password:
                    raise ValueError("Ejecuta primero python scripts/init_env.py.")
                user = add_user(db, "admin@example.com", settings.demo_password)
                print("Administrador creado." if user else "El administrador ya existe.")
                print("Cuenta: admin@example.com con la contraseña DEMO_PASSWORD de tu .env.")
                if "admin@example.com" not in [e.lower() for e in settings.admin_emails]:
                    print('Agrega ADMIN_EMAILS=["admin@example.com"] a tu .env para darle')
                    print("permisos de administrador.")
            elif args.command == "seed-showcase":
                if settings.session_cookie_secure:
                    raise ValueError("El seed de demostración solo se permite en el entorno local.")
                if not settings.demo_password:
                    raise ValueError("Ejecuta primero python scripts/init_env.py.")
                created = seed_showcase(db, settings.demo_password, add_user)
                print(
                    f"Datos de muestra: {created['users']} usuarios, "
                    f"{created['projects']} proyectos y "
                    f"{created['experiments']} experimentos nuevos."
                )
                print("Cuentas: ana@, luis@, maria@ y sofia@example.com con DEMO_PASSWORD.")
            else:
                if settings.session_cookie_secure:
                    raise ValueError("El seed de demostración solo se permite en el entorno local.")
                if not settings.demo_password:
                    raise ValueError("Ejecuta primero python scripts/init_env.py.")
                for email, name in [
                    ("ana@example.com", "Predicción de demanda"),
                    ("luis@example.com", "Clasificación de materiales"),
                ]:
                    user = add_user(db, email, settings.demo_password)
                    if user:
                        project = Project(
                            user_id=user.id,
                            name=name,
                            description="Datos ficticios para explorar LabTrack.",
                        )
                        db.add(project)
                        db.flush()
                        db.add(
                            Experiment(
                                project_id=project.id,
                                name="Línea base",
                                model="RandomForest",
                                dataset_version="demo-v1",
                                metric_name="F1",
                                metric_value=0.84,
                                notes="Ejemplo sintético; no se ejecutó un modelo.",
                            )
                        )
                print("Demo preparada. Cuentas: ana@example.com y luis@example.com.")
                print("La contraseña está en DEMO_PASSWORD de tu .env. No se publica en Git.")
            db.commit()
    except ValueError as error:
        parser.exit(1, f"{error}\n")
    finally:
        engine.dispose()


if __name__ == "__main__":
    main()
