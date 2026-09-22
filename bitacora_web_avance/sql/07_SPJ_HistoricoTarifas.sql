USE [dim_sis_puerto_v1]
GO

SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO

/*
================================================================================
PROCEDIMIENTO ALMACENADO: dbo.SPJ_HistoricoTarifas
OBJETIVO: Consultar todas las tarifas históricas de un año o de un ID
          con los campos necesarios para la tabla.
================================================================================
*/

IF OBJECT_ID('dbo.SPJ_HistoricoTarifas', 'P') IS NOT NULL
    DROP PROCEDURE dbo.SPJ_HistoricoTarifas;
GO

CREATE PROCEDURE [dbo].[SPJ_HistoricoTarifas]
    @id                INT = NULL,
    @ano               INT = NULL,
    @listarCabeceras   BIT = 0
AS
BEGIN
    SET NOCOUNT ON;

    -- 1. Si enviaron un año como primer parámetro posicional (ej. EXEC SPJ_HistoricoTarifas 2026)
    IF (@ano IS NULL AND @id >= 1900)
    BEGIN
        SET @ano = @id;
        SET @id = NULL;
    END;

    -- 2. Si no enviaron ni ID ni Año, tomar por defecto el año del último registro
    IF (@id IS NULL AND @ano IS NULL)
    BEGIN
        SELECT TOP 1 @ano = YEAR(fechaRegistro) FROM dbo.dim_TarifaCab ORDER BY id DESC;
    END;

    -- Cargar usuarios para obtener el nombre de quien registró el ajuste
    SELECT idusuario, MAX(nombre) AS nombre 
    INTO #UsuariosTarifa 
    FROM dbo.dim_con_mov_turno 
    WHERE idusuario IS NOT NULL
    GROUP BY idusuario;

    -- 3. Modo 1: Listado resumido de cabeceras históricas
    IF (@listarCabeceras = 1)
    BEGIN
        SELECT 
            C.id AS id_tarifaCab,
            C.idUsuario,
            COALESCE(U.nombre, '') AS nombre,
            C.fechaRegistro,
            YEAR(C.fechaRegistro) AS ano,
            C.porcentajeActual,
            C.detalle
        FROM dbo.dim_TarifaCab C 
        LEFT JOIN #UsuariosTarifa U ON C.idUsuario = U.idusuario
        ORDER BY C.fechaRegistro DESC, C.id DESC;

        DROP TABLE #UsuariosTarifa;
        RETURN;
    END;

    -- 4. Modo 2: Consulta de tarifas (todas las tarifas del año o del ID especificado)
    IF EXISTS (
        SELECT 1 
        FROM dbo.dim_TarifasAuditoria AUD
        INNER JOIN dbo.dim_TarifaCab CAB ON AUD.id_tarifaCab = CAB.id
        WHERE (@id IS NOT NULL AND CAB.id = @id)
           OR (@id IS NULL AND @ano IS NOT NULL AND YEAR(CAB.fechaRegistro) = @ano)
    )
    BEGIN
        SELECT 
            ROW_NUMBER() OVER (ORDER BY CAB.fechaRegistro DESC, TR.Sctarifa) AS Nro,
            CAB.idUsuario,
            COALESCE(U.nombre, '') AS nombre,
            CAB.fechaRegistro,
            TR.Sctarifa AS codigo,
            TR.tarifa,
            AUD.valor,
            TR.inflacion,
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
            CAB.id AS id_tarifaCab,
            CAB.porcentajeActual
        FROM dbo.dim_TarifasAuditoria AUD
        INNER JOIN dbo.dim_TarifaCab CAB ON AUD.id_tarifaCab = CAB.id
        INNER JOIN dbo.dim_tarifa TR ON AUD.idtarifa = TR.idtarifa
        LEFT JOIN #UsuariosTarifa U ON CAB.idUsuario = U.idusuario
        WHERE (@id IS NOT NULL AND CAB.id = @id)
           OR (@id IS NULL AND @ano IS NOT NULL AND YEAR(CAB.fechaRegistro) = @ano)
        ORDER BY CAB.fechaRegistro DESC, TR.Sctarifa;
    END
    ELSE
    BEGIN
        SELECT 
            ROW_NUMBER() OVER (ORDER BY CAB.fechaRegistro DESC, TR.Sctarifa) AS Nro,
            CAB.idUsuario,
            COALESCE(U.nombre, '') AS nombre,
            CAB.fechaRegistro,
            TR.Sctarifa AS codigo,
            TR.tarifa,
            TR.valor,
            TR.inflacion,
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
            CAB.id AS id_tarifaCab,
            CAB.porcentajeActual
        FROM dbo.dim_tarifa TR
        CROSS JOIN (
            SELECT id, fechaRegistro, porcentajeActual, idUsuario
            FROM dbo.dim_TarifaCab
            WHERE (@id IS NOT NULL AND id = @id)
               OR (@id IS NULL AND @ano IS NOT NULL AND YEAR(fechaRegistro) = @ano)
        ) CAB
        LEFT JOIN #UsuariosTarifa U ON CAB.idUsuario = U.idusuario
        WHERE TR.activo = 1
        ORDER BY CAB.fechaRegistro DESC, TR.Sctarifa;
    END

    DROP TABLE #UsuariosTarifa;
END;
GO
