USE [dim_sis_puerto_v1]
GO

/*
================================================================================
SCRIPT: 05_SPJ_insert_update_Tarifas_idestado.sql
OBJETIVO:
  Actualizar los procedimientos dbo.SPJ_insert_Tarifas y dbo.SPJ_Update_Tarifas
  para que gestionen internamente la asignación automática de:
    - idestado = 0 cuando @sactivo = 1 (Tarifa Activa / Vigente)
    - idestado = 7 cuando @sactivo = 0 (Tarifa Inactiva / Anulada)
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
    @sinflacion     INT = 0
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
            inflacion
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
            @sinflacion
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

PRINT 'Procedimiento [dbo].[SPJ_insert_Tarifas] actualizado exitosamente.';
GO


-- 2. PROCEDIMIENTO dbo.SPJ_Update_Tarifas
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO

CREATE OR ALTER PROCEDURE [dbo].[SPJ_Update_Tarifas]
@sidtarifa      int,
@sctarifa       nvarchar(5),
@starifa        nvarchar(80),
@svalor         decimal(10,4),
@scpartida      nvarchar(19),
@sidpartida     nvarchar(5),
@sidtasa        int,
@sformula       nvarchar(50),
@sdetalle       nvarchar(50),
@shora_dia      int,
@seslora_tneto  int,
@siva           int,
@stikect        int,
@sactivo	    int,
@scambioFactura int,
@sresul         int output,
@sinflacion     int = 0
AS
BEGIN
	set @sresul=1
	if not exists(select sctarifa from dim_tarifa where sctarifa=@sctarifa and idtasa=@sidtasa and idtarifa<>@sidtarifa)
       begin
	 	   if not exists(select tarifa from dim_tarifa where tarifa=@starifa and idtasa=@sidtasa and idtarifa<>@sidtarifa)
		      begin
                  DECLARE @calc_idestado INT;
                  SET @calc_idestado = CASE WHEN @sactivo = 1 THEN 0 ELSE 7 END;

				  update dim_tarifa set sctarifa=@sctarifa,tarifa=@starifa,
				  valor=@svalor,scpartida=@scpartida,formula=@sformula,
				  detalle=@sdetalle,idtasa=@sidtasa,idpartida=@sidpartida,
				  dia_hora=@shora_dia,eslora_toneto=@seslora_tneto,
				  iva=@siva,tikect=@stikect,activo=@sactivo,
                  idestado=@calc_idestado,
				  cambioFacturacion=@scambioFactura,
				  inflacion=@sinflacion
                  where idtarifa=@sidtarifa
				  set @sresul=20
			  end
		    else
              begin
                set @sresul=4
               end 
        end
	else
	  begin
        set @sresul=3
	  end
END;
GO

PRINT 'Procedimiento [dbo].[SPJ_Update_Tarifas] actualizado exitosamente.';
GO
