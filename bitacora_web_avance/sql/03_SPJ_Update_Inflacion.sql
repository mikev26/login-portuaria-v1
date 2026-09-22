USE [dim_sis_puerto_v1]
GO
/****** Objeto: StoredProcedure [dbo].[SPJ_Update_Inflacion] Fecha de script: 02/09/2026 ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
ALTER PROCEDURE [dbo].[SPJ_Update_Inflacion]
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
        INSERT INTO dbo.dim_TarifaCab (detalle, idUsuario, fechaInflacion, fechaRegistro, porcentajeAnterior, porcentajeActual)
        VALUES (@pdetalle, @pidusuario, @pfechaInflacion, GETDATE(), @porcentajeAnterior, @pinflacion);

        DECLARE @new_cab_id INT;
        SET @new_cab_id = SCOPE_IDENTITY();

        -- 3. Marcar auditorías anteriores de las tarifas activas como inactivas/históricas (idestado = 7)
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