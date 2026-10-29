-- Consultas para mostrar la base de datos de LabTrack en DBeaver (SQLite).
-- Conexión: data/labtrack.db. Ejecuta una consulta a la vez con Ctrl + Enter.

-- 1. Tablas de la base de datos
SELECT name AS tabla
FROM sqlite_master
WHERE type = 'table' AND name NOT LIKE 'sqlite_%'
ORDER BY name;

-- 2. Usuarios con cuántos proyectos y experimentos tiene cada uno
SELECT u.email,
       COUNT(DISTINCT p.id) AS proyectos,
       COUNT(e.id)          AS experimentos
FROM users u
LEFT JOIN projects p    ON p.user_id = u.id
LEFT JOIN experiments e ON e.project_id = p.id
GROUP BY u.id
ORDER BY u.email;

-- 3. Las contraseñas no se guardan: solo su hash Argon2
SELECT email, substr(password_hash, 1, 32) || '…' AS hash_argon2
FROM users
ORDER BY email;

-- 4. Experimentos de un proyecto, unidos con su proyecto y su dueño
SELECT u.email AS duenio, p.name AS proyecto, e.name AS experimento,
       e.model, e.dataset_version, e.metric_name, e.metric_value, e.status, e.created_at
FROM experiments e
JOIN projects p ON p.id = e.project_id
JOIN users u    ON u.id = p.user_id
WHERE u.email = 'diego@example.com' AND p.name = 'GreenSense · humedad del sustrato'
ORDER BY e.created_at;

-- 5. Persistencia en vivo: el último experimento guardado desde la app
SELECT e.id, p.name AS proyecto, e.name, e.model, e.metric_value, e.status, e.created_at
FROM experiments e
JOIN projects p ON p.id = e.project_id
ORDER BY e.id DESC
LIMIT 5;

-- 6. Relación y regla de borrado: experiments.project_id → projects.id con ON DELETE RESTRICT
PRAGMA foreign_key_list('experiments');

-- 7. Migraciones: versión aplicada y la columna status del ejercicio 4
SELECT version_num AS migracion_aplicada FROM alembic_version;
SELECT name AS columna, type AS tipo, "notnull" AS obligatoria, dflt_value AS valor_por_defecto
FROM pragma_table_info('experiments');

-- 8. Experimentos por estado
SELECT status, COUNT(*) AS total
FROM experiments
GROUP BY status;

-- 9. Sesiones: se guarda el hash del token, nunca el token
SELECT u.email, substr(s.token_hash, 1, 16) || '…' AS hash_del_token, s.expires_at
FROM auth_sessions s
JOIN users u ON u.id = s.user_id
ORDER BY s.expires_at DESC;
