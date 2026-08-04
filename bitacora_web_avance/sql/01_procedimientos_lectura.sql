/*
PROCEDIMIENTOS DE SOLO LECTURA PARA DJANGO
Base: dim_sis_puerto_v1
No modifican información.
El ingeniero de base de datos debe revisar y ejecutar este script.
*/
USE dim_sis_puerto_v1;
GO

CREATE OR ALTER PROCEDURE dbo.sp_bitacora_turnos_activos
    @idusuario INT
AS
BEGIN
    SET NOCOUNT ON;

    SELECT
        idusuario,
        fecha_i,
        fecha_s,
        idestado,
        nombre,
        idturno,
        usuario,
        numero,
        cargo,
        activo,
        Bitacora
    FROM dbo.dim_con_mov_turno
    WHERE fecha_s IS NULL
      AND activo <> 7
      AND Bitacora = 1
      AND idusuario = @idusuario
    ORDER BY fecha_i DESC;
END;
GO

CREATE OR ALTER PROCEDURE dbo.sp_bitacora_buques_industriales
AS
BEGIN
    SET NOCOUNT ON;

    SELECT
        sgregistro AS scbuque,
        buque AS nombre,
        n_matricula,
        fecha_arrivo,
        0 AS cabo,
        idbuque,
        idregistro
    FROM dbo.dim_con_maestro_registro_lista
    WHERE fecha_zarpe IS NULL
      AND idestado <> 7
    ORDER BY fecha_arrivo DESC, buque;
END;
GO

CREATE OR ALTER PROCEDURE dbo.sp_bitacora_buques_artesanales
AS
BEGIN
    SET NOCOUNT ON;

    SELECT
        sgregistro AS scbuque,
        buque AS nombre,
        n_matricula,
        fecha_ing AS fecha_arrivo,
        0 AS cabo,
        idbuque,
        sgregistro AS idregistro
    FROM dbo.dim_con_maestro_registro_cabotaje
    WHERE fecha_salida IS NULL
      AND idestado <> 7
    ORDER BY fecha_ing DESC, buque;
END;
GO

-- No otorgar permisos a PUBLIC.
-- Reemplazar USUARIO_APP por el usuario técnico usado por Django, si corresponde:
-- GRANT EXECUTE ON dbo.sp_bitacora_turnos_activos TO USUARIO_APP;
-- GRANT EXECUTE ON dbo.sp_bitacora_buques_industriales TO USUARIO_APP;
-- GRANT EXECUTE ON dbo.sp_bitacora_buques_artesanales TO USUARIO_APP;
