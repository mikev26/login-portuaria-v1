USE [dim_sis_puerto_v1]
GO

SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO

/*
================================================================================
SCRIPT: 06_alter_SPJ_v_tarifas_inflacion.sql
OBJETIVO:
  Actualizar el procedimiento almacenado dbo.SPJ_v_tarifas para que:
    1. Filtre estrictamente por el campo 'activo' (activo = 1 para activas,
       activo = 0 para inactivas/anuladas), sin utilizar 'idestado'.
    2. En @estado = 101 devuelva todas las tarifas activas (activo = 1),
       incluyendo tanto las que tienen inflacion = 1 como inflacion = 0,
       junto con la columna inflacion para el frontend.
================================================================================
*/

ALTER PROCEDURE [dbo].[SPJ_v_tarifas]
    @estado INT 
AS
BEGIN
    SET NOCOUNT ON;
    
    -- 1. Todas las tarifas (activas e inactivas)
    IF (@estado = 100)
    BEGIN
        SELECT 
            T.sctarifa, 
            T.tarifa, 
            T.valor, 
            T.formula,
            CASE WHEN T.inflacion = 1 THEN 'Aplica inflación anual' ELSE 'No aplica Inflación anual' END AS AplicaInflacion,
            T.detalle, 
            T.iva, 
            P.scpartida, 
            P.Partida,
            P.cedulaFinanza, 
            T.activo, 
            T.ptipo, 
            T.dia_hora, 
            T.eslora_toneto, 
            T.idtarifa, 
            P.idpartida,
            T.idtasa, 
            T.tikect,
            T.inflacion
        FROM dbo.dim_tarifa T 
        LEFT JOIN dbo.dim_partida P ON T.idpartida = P.idpartida;
    END;

    -- 2. Registro de Inflación: Todas las tarifas activas (activo = 1)
    IF (@estado = 101)
    BEGIN
        SELECT 
            ROW_NUMBER() OVER (ORDER BY TR.Sctarifa) AS Nro,
            TS.Tasa,
            TR.Sctarifa,
            TR.tarifa,
            TR.valor,
            TR.inflacion,
            CASE WHEN TR.inflacion = 1 THEN 'Aplica inflación anual' ELSE 'No aplica Inflación anual' END AS AplicaInflacion,
            CAST(0.0000 AS DECIMAL(12,4)) AS TarifaInflacion,
            CAST(0.0000 AS DECIMAL(12,4)) AS ValorFinalTarifa,
            TR.idtarifa,
            TR.idtasa,
            TR.activo
        FROM dbo.dim_tarifa TR
        LEFT JOIN dbo.dim_tasa TS ON TR.idtasa = TS.idtasa
        WHERE TR.activo = 1
        ORDER BY TR.Sctarifa;
    END;

    -- 3. Tarifas por estado del campo activo (1 Activa / 0 Anulada o Inactiva)
    IF (@estado >= 0 AND @estado < 2)
    BEGIN
        SELECT 
            T.sctarifa, 
            T.tarifa, 
            T.valor, 
            T.formula, 
            CASE WHEN T.inflacion = 1 THEN 'Aplica inflación anual' ELSE 'No aplica Inflación anual' END AS AplicaInflacion,
            T.detalle, 
            T.iva,  
            P.scpartida, 
            P.Partida, 
            P.cedulaFinanza, 
            T.activo, 
            T.ptipo, 
            T.dia_hora, 
            T.eslora_toneto, 
            T.idtarifa, 
            P.idpartida,
            T.idtasa, 
            T.tikect,
            T.inflacion
        FROM dbo.dim_tarifa T 
        LEFT JOIN dbo.dim_partida P ON T.idpartida = P.idpartida 
        WHERE T.activo = @estado;
    END;
END;
GO

PRINT 'Procedimiento [dbo].[SPJ_v_tarifas] actualizado exitosamente con filtro estricto por campo activo.';
GO
