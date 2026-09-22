USE [dim_sis_puerto_v1]
GO

/*
================================================================================
SCRIPT: 08_alter_SPJ_insert_update_Tarifas_ptipo.sql
OBJETIVO:
  Actualizar los procedimientos dbo.SPJ_insert_Tarifas y dbo.SPJ_Update_Tarifas
  para incorporar el parámetro @sptipo INT = 0 que gestiona la columna [ptipo]
  en la tabla dbo.dim_tarifa:
    - Eslora:       ptipo = 1
    - T.Neto:       ptipo = 2
    - Ton.Bruto:    ptipo = 0
    - Otros:        ptipo = 0
================================================================================
*/

-- 1. PROCEDIMIENTO dbo.SPJ_insert_Tarifas
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO

CREATE OR ALTER PROCEDURE [dbo].[SPJ_insert_Tarifas]
    @sctarifa       NVARCHAR(5),
    @starifa        NVARCHAR(80),
    @svalor         DECIMAL(12,4),
    @scpartida      NVARCHAR(19),
    @sidpartida     NVARCHAR(5),
    @sidtasa        INT,
    @sformula       NVARCHAR(50),
    @sdetalle       NVARCHAR(50),
    @shora_dia      INT,
    @seslora_tneto  INT,
    @siva           INT,
    @stikect        INT,
    @sactivo        INT,
    @scambioFactura INT,
    @sresul         INT OUTPUT,
    @sinflacion     INT = 0,
    @sptipo         INT = 0
AS
BEGIN
    SET NOCOUNT ON;
    SET XACT_ABORT ON;

    SET @sresul = 1;

    BEGIN TRY

        BEGIN TRANSACTION;

        IF EXISTS
        (
            SELECT 1
            FROM dbo.dim_tarifa
            WHERE sctarifa = @sctarifa
              AND idtasa = @sidtasa
        )
        BEGIN
            SET @sresul = 3;

            COMMIT TRANSACTION;
            RETURN;
        END;

        IF EXISTS
        (
            SELECT 1
            FROM dbo.dim_tarifa
            WHERE tarifa = @starifa
              AND idtasa = @sidtasa
        )
        BEGIN
            SET @sresul = 4;

            COMMIT TRANSACTION;
            RETURN;
        END;

        DECLARE @calc_idestado INT;
        SET @calc_idestado = CASE WHEN @sactivo = 1 THEN 0 ELSE 7 END;

        INSERT INTO dbo.dim_tarifa
        (
            sctarifa,
            tarifa,
            valor,
            scpartida,
            formula,
            detalle,
            idtasa,
            idpartida,
            dia_hora,
            eslora_toneto,
            iva,
            tikect,
            activo,
            idestado,
            cambioFacturacion,
            sidtarifa,
            inflacion,
            ptipo
        )
        VALUES
        (
            @sctarifa,
            @starifa,
            @svalor,
            @scpartida,
            @sformula,
            @sdetalle,
            @sidtasa,
            @sidpartida,
            @shora_dia,
            @seslora_tneto,
            @siva,
            @stikect,
            @sactivo,
            @calc_idestado,
            @scambioFactura,
            0,
            @sinflacion,
            @sptipo
        );

        SET @sresul = CONVERT(INT, SCOPE_IDENTITY()) + 5;

        COMMIT TRANSACTION;

    END TRY
    BEGIN CATCH

        IF XACT_STATE() <> 0
            ROLLBACK TRANSACTION;

        SET @sresul = -1;

        THROW;

    END CATCH;
END;
GO

PRINT 'Procedimiento [dbo].[SPJ_insert_Tarifas] actualizado exitosamente con soporte para [ptipo].';
GO


-- 2. PROCEDIMIENTO dbo.SPJ_Update_Tarifas
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO

CREATE OR ALTER PROCEDURE [dbo].[SPJ_Update_Tarifas]
    @sidtarifa      INT,
    @sctarifa       NVARCHAR(5),
    @starifa        NVARCHAR(80),
    @svalor         DECIMAL(10,4),
    @scpartida      NVARCHAR(19),
    @sidpartida     NVARCHAR(5),
    @sidtasa        INT,
    @sformula       NVARCHAR(50),
    @sdetalle       NVARCHAR(50),
    @shora_dia      INT,
    @seslora_tneto  INT,
    @siva           INT,
    @stikect        INT,
    @sactivo        INT,
    @scambioFactura INT,
    @sresul         INT OUTPUT,
    @sinflacion     INT = 0,
    @sptipo         INT = 0
AS
BEGIN
    SET @sresul = 1;

    IF NOT EXISTS (SELECT 1 FROM dbo.dim_tarifa WHERE sctarifa = @sctarifa AND idtasa = @sidtasa AND idtarifa <> @sidtarifa)
    BEGIN
        IF NOT EXISTS (SELECT 1 FROM dbo.dim_tarifa WHERE tarifa = @starifa AND idtasa = @sidtasa AND idtarifa <> @sidtarifa)
        BEGIN
            DECLARE @calc_idestado INT;
            SET @calc_idestado = CASE WHEN @sactivo = 1 THEN 0 ELSE 7 END;

            UPDATE dbo.dim_tarifa
            SET sctarifa          = @sctarifa,
                tarifa            = @starifa,
                valor             = @svalor,
                scpartida         = @scpartida,
                formula           = @sformula,
                detalle           = @sdetalle,
                idtasa            = @sidtasa,
                idpartida         = @sidpartida,
                dia_hora          = @shora_dia,
                eslora_toneto     = @seslora_tneto,
                iva               = @siva,
                tikect            = @stikect,
                activo            = @sactivo,
                idestado          = @calc_idestado,
                cambioFacturacion = @scambioFactura,
                inflacion         = @sinflacion,
                ptipo             = @sptipo
            WHERE idtarifa = @sidtarifa;

            SET @sresul = 20;
        END
        ELSE
        BEGIN
            SET @sresul = 4;
        END;
    END
    ELSE
    BEGIN
        SET @sresul = 3;
    END;
END;
GO

PRINT 'Procedimiento [dbo].[SPJ_Update_Tarifas] actualizado exitosamente con soporte para [ptipo].';
GO
