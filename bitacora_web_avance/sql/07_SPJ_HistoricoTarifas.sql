USE [dim_sis_puerto_v1]
GO

SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO

/*
================================================================================
PROCEDIMIENTO ALMACENADO: dbo.SPJ_HistoricoTarifas
OBJETIVO: Consultar el histórico de tarifas e inflación congeladas por ID de cabecera.
================================================================================
*/

IF OBJECT_ID('dbo.SPJ_HistoricoTarifas', 'P') IS NOT NULL
    DROP PROCEDURE dbo.SPJ_HistoricoTarifas;
GO

CREATE PROCEDURE [dbo].[SPJ_HistoricoTarifas]
    @id                INT = NULL,
    @id_tarifaCab      INT = NULL,
    @idCabotaje        INT = NULL,
    @id_tarifaCabotaje INT = NULL,
    @ano               INT = NULL,
    @anio              INT = NULL,
    @listarCabeceras   BIT = 0
AS
BEGIN
    SET NOCOUNT ON;

    -- 1. Resolver el ID o el Año a consultar
    DECLARE @idCab INT = COALESCE(@id, @id_tarifaCab, @idCabotaje, @id_tarifaCabotaje);
    DECLARE @targetAno INT = COALESCE(@ano, @anio);

    -- 2. Si se solicita listar el historial de cabeceras
    IF (@listarCabeceras = 1 OR @idCab = -1)
    BEGIN
        SELECT 
            id AS id_tarifaCab,
            id AS idCabotaje,
            id AS id,
            ano AS anio_actual,
            ano AS ano,
            (ano - 1) AS anio_anterior,
            porcentajeActual AS porcentaje_inflacion,
            porcentajeActual AS porcentaje_actual,
            porcentajeAnterior,
            detalle,
            fechaInflacion,
            fechaRegistro,
            idUsuario
        FROM dbo.dim_TarifaCab
        ORDER BY ano DESC, id DESC;
        RETURN;
    END;

    -- 3. Si no se especificó ID ni Año, tomar la última cabecera registrada por defecto
    IF ((@idCab IS NULL OR @idCab = 0) AND (@targetAno IS NULL OR @targetAno = 0))
    BEGIN
        SELECT TOP 1 @idCab = id FROM dbo.dim_TarifaCab ORDER BY id DESC;
    END;

    -- 4. Consulta de tarifas históricas por ID de cabecera o por Año completo
    IF EXISTS (
        SELECT 1 
        FROM dbo.dim_TarifasAuditoria AUD
        INNER JOIN dbo.dim_TarifaCab CAB ON AUD.id_tarifaCab = CAB.id
        WHERE (@idCab IS NOT NULL AND CAB.id = @idCab)
           OR (@idCab IS NULL AND @targetAno IS NOT NULL AND CAB.ano = @targetAno)
    )
    BEGIN
        SELECT 
            ROW_NUMBER() OVER (ORDER BY CAB.fechaRegistro DESC, TR.Sctarifa) AS Nro,
            TS.Tasa,
            TR.Sctarifa,
            TR.Sctarifa AS codigo,
            TR.tarifa,
            AUD.valor AS valor,
            AUD.valor AS valor_anterior,
            TR.inflacion,
            CASE 
                WHEN TR.inflacion = 1 THEN 'Aplica inflación anual' 
                ELSE 'No aplica Inflación anual' 
            END AS AplicaInflacion,
            CASE 
                WHEN TR.inflacion = 1 THEN CAB.porcentajeActual
                ELSE CAST(0.0000 AS DECIMAL(12,4))
            END AS porcentajeInflacion,
            CASE 
                WHEN TR.inflacion = 1 
                    THEN CAST(ROUND(AUD.valor * (CAB.porcentajeActual / 100.00), 4) AS DECIMAL(12,4))
                ELSE CAST(0.0000 AS DECIMAL(12,4))
            END AS TarifaInflacion,
            CASE 
                WHEN TR.inflacion = 1 
                    THEN CAST(ROUND(AUD.valor * (1.0 + (CAB.porcentajeActual / 100.00)), 4) AS DECIMAL(12,4))
                ELSE AUD.valor
            END AS ValorFinalTarifa,
            TR.idtarifa,
            TR.idtasa,
            TR.activo,
            CAB.id AS id_tarifaCab,
            CAB.id AS idCabotaje,
            CAB.id AS id,
            CAB.ano,
            (CAB.ano - 1) AS ano_anterior,
            CAB.fechaInflacion,
            CAB.fechaRegistro,
            CAB.detalle,
            CAB.porcentajeActual,
            CAB.porcentajeAnterior,
            CAB.idUsuario,
            CAB.idUsuario AS id_usuario
        FROM dbo.dim_TarifasAuditoria AUD
        INNER JOIN dbo.dim_TarifaCab CAB ON AUD.id_tarifaCab = CAB.id
        INNER JOIN dbo.dim_tarifa TR ON AUD.idtarifa = TR.idtarifa
        LEFT JOIN dbo.dim_tasa TS ON TR.idtasa = TS.idtasa
        WHERE (@idCab IS NOT NULL AND CAB.id = @idCab)
           OR (@idCab IS NULL AND @targetAno IS NOT NULL AND CAB.ano = @targetAno)
        ORDER BY CAB.fechaRegistro DESC, TR.Sctarifa;
    END
    ELSE
    BEGIN
        SELECT 
            ROW_NUMBER() OVER (ORDER BY TR.Sctarifa) AS Nro,
            TS.Tasa,
            TR.Sctarifa,
            TR.Sctarifa AS codigo,
            TR.tarifa,
            TR.valor AS valor,
            TR.valor AS valor_anterior,
            TR.inflacion,
            CASE 
                WHEN TR.inflacion = 1 THEN 'Aplica inflación anual' 
                ELSE 'No aplica Inflación anual' 
            END AS AplicaInflacion,
            CASE 
                WHEN TR.inflacion = 1 THEN CAB.porcentajeActual
                ELSE CAST(0.0000 AS DECIMAL(12,4))
            END AS porcentajeInflacion,
            CASE 
                WHEN TR.inflacion = 1 
                    THEN CAST(ROUND(TR.valor * (CAB.porcentajeActual / 100.00), 4) AS DECIMAL(12,4))
                ELSE CAST(0.0000 AS DECIMAL(12,4))
            END AS TarifaInflacion,
            CASE 
                WHEN TR.inflacion = 1 
                    THEN CAST(ROUND(TR.valor * (1.0 + (CAB.porcentajeActual / 100.00)), 4) AS DECIMAL(12,4))
                ELSE TR.valor
            END AS ValorFinalTarifa,
            TR.idtarifa,
            TR.idtasa,
            TR.activo,
            CAB.id AS id_tarifaCab,
            CAB.id AS idCabotaje,
            CAB.id AS id,
            CAB.ano,
            (CAB.ano - 1) AS ano_anterior,
            CAB.fechaInflacion,
            CAB.fechaRegistro,
            CAB.detalle,
            CAB.porcentajeActual,
            CAB.porcentajeAnterior,
            CAB.idUsuario,
            CAB.idUsuario AS id_usuario
        FROM dbo.dim_tarifa TR
        LEFT JOIN dbo.dim_tasa TS ON TR.idtasa = TS.idtasa
        CROSS JOIN (
            SELECT TOP 1 id, ano, detalle, fechaInflacion, porcentajeActual, porcentajeAnterior, fechaRegistro, idUsuario
            FROM dbo.dim_TarifaCab
            WHERE (@idCab IS NOT NULL AND id = @idCab) OR (@idCab IS NULL AND @targetAno IS NOT NULL AND ano = @targetAno)
            ORDER BY id DESC
        ) CAB
        WHERE TR.activo = 1
        ORDER BY TR.Sctarifa;
    END

END;
GO
