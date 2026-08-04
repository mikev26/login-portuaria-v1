/*
DIAGNÓSTICO DE AUTENTICACIÓN — SOLO LECTURA
Ejecutar primero en la base op_claves.
No consulta ni muestra valores de contraseñas.
*/
USE op_claves;
GO

-- 1. Buscar procedimientos existentes relacionados con el login.
SELECT
    DB_NAME() AS base_datos,
    s.name AS esquema,
    p.name AS procedimiento,
    p.create_date,
    p.modify_date
FROM sys.procedures AS p
INNER JOIN sys.schemas AS s ON s.schema_id = p.schema_id
WHERE p.name LIKE '%login%'
   OR p.name LIKE '%usuario%'
   OR p.name LIKE '%clave%'
   OR p.name LIKE '%acceso%'
   OR p.name LIKE '%valid%'
ORDER BY p.name;
GO

-- 2. Ver parámetros de esos procedimientos.
SELECT
    s.name AS esquema,
    p.name AS procedimiento,
    prm.parameter_id,
    prm.name AS parametro,
    TYPE_NAME(prm.user_type_id) AS tipo,
    prm.max_length,
    prm.is_output
FROM sys.procedures AS p
INNER JOIN sys.schemas AS s ON s.schema_id = p.schema_id
LEFT JOIN sys.parameters AS prm ON prm.object_id = p.object_id
WHERE p.name LIKE '%login%'
   OR p.name LIKE '%usuario%'
   OR p.name LIKE '%clave%'
   OR p.name LIKE '%acceso%'
   OR p.name LIKE '%valid%'
ORDER BY p.name, prm.parameter_id;
GO

-- 3. Ver únicamente la estructura de las tablas relacionadas.
SELECT
    TABLE_SCHEMA,
    TABLE_NAME,
    COLUMN_NAME,
    DATA_TYPE,
    CHARACTER_MAXIMUM_LENGTH,
    IS_NULLABLE
FROM INFORMATION_SCHEMA.COLUMNS
WHERE TABLE_NAME IN ('dim_usuarios', 'dim_claves', 'opc_accesos')
ORDER BY TABLE_NAME, ORDINAL_POSITION;
GO

-- 4. Cuando identifiques un procedimiento candidato, reemplaza el nombre:
-- EXEC sys.sp_help 'dbo.NOMBRE_PROCEDIMIENTO';
-- EXEC sys.sp_helptext 'dbo.NOMBRE_PROCEDIMIENTO';
--
-- Entregar al desarrollador:
-- a) nombre completo; b) parámetros en orden; c) ejemplo EXEC;
-- d) columnas que devuelve con credenciales válidas e inválidas.
