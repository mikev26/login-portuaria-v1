USE [dim_sis_puerto_v1]
GO

/*
================================================================================
SCRIPT: 04_alter_dim_TarifasAuditoria_idestado.sql
OBJETIVO:
  1. Agregar el campo 'idestado' a la tabla dim_TarifasAuditoria con valor por defecto 0.
  2. Actualizar el Stored Procedure dbo.SPJ_Update_Inflacion para:
     - Filtrar tarifas activas únicamente por [activo = 1] en dbo.dim_tarifa.
     - Asignar idestado = 7 a las auditorías previas de las tarifas que se van a actualizar.
     - Asignar idestado = 0 a las nuevas auditorías vinculadas al nuevo id_tarifaCab.
================================================================================
*/

-- 1. Agregar columna idestado a dim_TarifasAuditoria si no existe
IF NOT EXISTS (
    SELECT 1 
    FROM sys.columns 
    WHERE object_id = OBJECT_ID('dbo.dim_TarifasAuditoria') 
      AND name = 'idestado'
)
BEGIN
    ALTER TABLE dbo.dim_TarifasAuditoria 
    ADD idestado INT NOT NULL CONSTRAINT DF_dim_TarifasAuditoria_idestado DEFAULT 0;

    PRINT 'Columna [idestado] agregada exitosamente a [dbo].[dim_TarifasAuditoria].';
END
ELSE
BEGIN
    PRINT 'La columna [idestado] ya existe en [dbo].[dim_TarifasAuditoria].';
END
GO

-- 2. Asegurar que cualquier registro anterior sin estado tenga idestado = 7 o 0 según corresponda
UPDATE dbo.dim_TarifasAuditoria
SET idestado = 0
WHERE idestado IS NULL;
GO

-- 3. Actualizar / Crear el Stored Procedure dbo.SPJ_Update_Inflacion
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO

CREATE OR ALTER PROCEDURE [dbo].[SPJ_Update_Inflacion]
    @pinflacion DECIMAL(10,4),
    @pano int,
    @pidusuario int,
    @pdetalle NVARCHAR(252) = NULL,
    @pfechaInflacion DATE = NULL,
    @sresul INT OUTPUT
AS
BEGIN
    SET NOCOUNT ON;
    SET @sresul = 1;
    BEGIN TRY
        -- 1. Obtener el porcentaje de inflación anterior de las tarifas activas
        DECLARE @porcentajeAnterior DECIMAL(12,4);
        SELECT TOP 1 @porcentajeAnterior = porcentajeInflacion 
        FROM dbo.dim_tarifa 
        WHERE inflacion = 1 AND activo = 1;

        IF @porcentajeAnterior IS NULL SET @porcentajeAnterior = 0;

        -- 2. Insertar cabecera del ajuste por inflación
        INSERT INTO dbo.dim_TarifaCab (ano, detalle, idUsuario, fechaInflacion, fechaRegistro, porcentajeAnterior, porcentajeActual)
        VALUES (@pano, @pdetalle, @pidusuario, @pfechaInflacion, GETDATE(), @porcentajeAnterior, @pinflacion);

        DECLARE @new_cab_id INT;
        SET @new_cab_id = SCOPE_IDENTITY();

        -- 3. Marcar auditorías anteriores de las tarifas afectadas como inactivas/históricas (idestado = 7)
        UPDATE dbo.dim_TarifasAuditoria
        SET idestado = 7
        WHERE idestado <> 7
          AND idtarifa IN (
              SELECT idtarifa 
              FROM dbo.dim_tarifa 
              WHERE inflacion = 1 AND activo = 1
          );

        -- 4. Guardar el nuevo detalle de tarifas (auditoría) con estado vigente (idestado = 0)
        INSERT INTO dbo.dim_TarifasAuditoria (id_tarifaCab, idtarifa, valor, idestado)
            SELECT @new_cab_id, idtarifa, valor, 0
            FROM dbo.dim_tarifa
            WHERE inflacion = 1 AND activo = 1;
       
        -- 5. Actualizar el valor y porcentaje de las tarifas activas
        UPDATE dbo.dim_tarifa
        SET valor = CAST(valor * (1.0 + (@pinflacion / 100.00)) AS DECIMAL(10,4)), porcentajeInflacion = @pinflacion
        WHERE inflacion = 1
          AND activo = 1;

    END TRY
    BEGIN CATCH
        SET @sresul = -1;
    END CATCH
END;
GO

PRINT 'Procedimiento [dbo].[SPJ_Update_Inflacion] actualizado exitosamente.';
GO
