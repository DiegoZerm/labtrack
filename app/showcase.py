"""Datos ficticios abundantes para demostrar LabTrack con la interfaz llena.

Los valores son sintéticos: ningún modelo se entrenó. La generación es
determinista y se puede ejecutar varias veces sin duplicar registros.
"""

import random
from datetime import timedelta

from sqlalchemy import select

from app.models import Experiment, Project, User, utcnow

# (modelo, ajuste aproximado de la métrica respecto a la línea base)
TREES = [("RandomForest", 0.0), ("XGBoost", 0.03), ("LightGBM", 0.025), ("ExtraTrees", -0.01)]
LINEAR = [("LogisticRegression", -0.04), ("SVM", -0.02), ("KNN", -0.05)]
NEURAL = [("MLP", 0.01), ("CNN", 0.05), ("ResNet18", 0.07), ("LSTM", 0.04)]
REGRESSORS = [("LinearRegression", 0.0), ("Ridge", -0.02), ("RandomForest", -0.08)]
REGRESSORS += [("XGBoost", -0.12), ("Prophet", -0.05), ("LSTM", -0.1)]

STEPS = [
    ("Línea base", "Configuración por defecto para tener un punto de comparación."),
    ("Ajuste de hiperparámetros", "Búsqueda aleatoria de 50 combinaciones."),
    ("Validación cruzada 5-fold", "Se reporta el promedio de los cinco pliegues."),
    ("Sin valores atípicos", "Se descartaron registros fuera de 3 desviaciones estándar."),
    ("Normalización min-max", "Escalado de variables numéricas entre 0 y 1."),
    ("Selección de variables", "Se conservaron las 20 variables más importantes."),
    ("Balanceo de clases", "Sobremuestreo de la clase minoritaria en entrenamiento."),
    ("Regularización L2", "Penalización para reducir el sobreajuste."),
    ("Early stopping", "Se detuvo el entrenamiento al no mejorar en 10 épocas."),
    ("Más datos", "Se agregó el lote nuevo del dataset."),
    ("Ensamble", "Promedio de los tres mejores modelos anteriores."),
    ("Prueba final", "Evaluación en el conjunto de prueba reservado."),
]

# correo: [(proyecto, descripción, dataset, métrica, base, mayor_es_mejor, modelos, cantidad)]
CATALOG = {
    "ana@example.com": [
        (
            "Pronóstico de ventas",
            "Ventas semanales por sucursal para planear inventario.",
            "ventas",
            "RMSE",
            142.0,
            False,
            REGRESSORS,
            10,
        ),
        (
            "Clasificación de reseñas",
            "Sentimiento positivo, neutro o negativo en reseñas.",
            "resenas",
            "F1",
            0.78,
            True,
            LINEAR + NEURAL,
            9,
        ),
        (
            "Detección de fraude",
            "Transacciones con tarjeta marcadas como sospechosas.",
            "transacciones",
            "AUC",
            0.86,
            True,
            TREES + LINEAR,
            11,
        ),
        (
            "Abandono de clientes",
            "Probabilidad de que un cliente cancele su suscripción.",
            "clientes",
            "F1",
            0.71,
            True,
            TREES,
            8,
        ),
        (
            "Consumo energético",
            "Consumo eléctrico horario de un edificio del campus.",
            "energia",
            "MAE",
            3.4,
            False,
            REGRESSORS,
            7,
        ),
        (
            "Calidad del aire",
            "Nivel de PM2.5 a partir de sensores de la ciudad.",
            "aire",
            "R2",
            0.62,
            True,
            REGRESSORS,
            6,
        ),
    ],
    "luis@example.com": [
        (
            "Microscopía de materiales",
            "Tipo de material a partir de imágenes de microscopio.",
            "materiales",
            "Accuracy",
            0.81,
            True,
            NEURAL + TREES,
            9,
        ),
        (
            "Defectos en piezas",
            "Piezas con defectos en la línea de producción.",
            "piezas",
            "Recall",
            0.74,
            True,
            NEURAL,
            7,
        ),
        (
            "Mantenimiento predictivo",
            "Horas restantes antes de la falla de un motor.",
            "motores",
            "RMSE",
            38.0,
            False,
            REGRESSORS,
            8,
        ),
        (
            "Rendimiento de cultivos",
            "Toneladas por hectárea según clima y suelo.",
            "cultivos",
            "MAE",
            0.9,
            False,
            REGRESSORS,
            5,
        ),
    ],
    "maria@example.com": [
        (
            "Diagnóstico de retinopatía",
            "Grado de retinopatía diabética en fondos de ojo.",
            "retina",
            "AUC",
            0.88,
            True,
            NEURAL,
            8,
        ),
        (
            "Readmisión hospitalaria",
            "Pacientes que regresan en menos de 30 días.",
            "pacientes",
            "F1",
            0.64,
            True,
            TREES + LINEAR,
            7,
        ),
        (
            "Tiempo de espera en urgencias",
            "Minutos estimados de espera por turno.",
            "urgencias",
            "MAE",
            21.0,
            False,
            REGRESSORS,
            6,
        ),
    ],
    "sofia@example.com": [
        (
            "Recomendación de cursos",
            "Cursos sugeridos según el historial del estudiante.",
            "inscripciones",
            "Precision",
            0.58,
            True,
            TREES + NEURAL,
            7,
        ),
        (
            "Deserción escolar",
            "Estudiantes en riesgo de abandonar el semestre.",
            "estudiantes",
            "Recall",
            0.69,
            True,
            TREES + LINEAR,
            8,
        ),
    ],
}


def _value(rng, base, higher_is_better, gain, progress):
    # La métrica mejora con las iteraciones, con ruido; nunca sale del rango válido.
    if higher_is_better:
        value = base + gain + 0.12 * (1 - base) * progress + rng.uniform(-0.015, 0.015)
        return round(min(max(value, 0.05), 0.995), 3)
    value = base * (1 + gain - 0.25 * progress + rng.uniform(-0.03, 0.03))
    return round(max(value, 0.01), 2 if base >= 10 else 3)


def seed_showcase(db, password, add_user):
    rng = random.Random(2026)
    now = utcnow()
    created = {"users": 0, "projects": 0, "experiments": 0}
    for email, projects in CATALOG.items():
        user = add_user(db, email, password)
        if user:
            created["users"] += 1
        else:
            user = db.scalar(select(User).where(User.email == email))
        for p_index, (name, description, dataset, metric, base, higher, models, count) in enumerate(
            projects
        ):
            project = db.scalar(
                select(Project).where(Project.user_id == user.id, Project.name == name)
            )
            start = now - timedelta(days=60 - p_index * 6, hours=rng.randint(0, 12))
            if project is None:
                project = Project(
                    user_id=user.id, name=name, description=description, created_at=start
                )
                db.add(project)
                db.flush()
                created["projects"] += 1
            existing = set(
                db.scalars(select(Experiment.name).where(Experiment.project_id == project.id))
            )
            for i, (step, note) in enumerate(STEPS[:count]):
                model, gain = models[i % len(models)]
                exp_name = f"{step} · {model}"
                if exp_name in existing:
                    continue
                version = 1 + i * 3 // count
                db.add(
                    Experiment(
                        project_id=project.id,
                        name=exp_name,
                        model=model,
                        dataset_version=f"{dataset}-v{version}",
                        metric_name=metric,
                        metric_value=_value(rng, base, higher, gain, i / max(count - 1, 1)),
                        notes=note,
                        created_at=start + timedelta(days=i * 2 + 1, hours=rng.randint(8, 19)),
                    )
                )
                created["experiments"] += 1
    return created
