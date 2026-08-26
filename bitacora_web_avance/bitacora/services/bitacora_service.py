"""Servicios para registro e historial de la bitácora."""

from __future__ import annotations

from datetime import datetime

from .db_connection import execute_procedure, execute_query

def obtener_fecha_hora_servidor():
    rows = execute_query(
        """
        SELECT GETDATE() AS fecha_hora_sql
        """
    )

    if not rows:
        raise RuntimeError(
            "SQL Server no devolvió la fecha y hora actual."
        )

    fecha_hora = rows[0].get("fecha_hora_sql")

    if fecha_hora is None:
        raise RuntimeError(
            "No fue posible obtener la fecha y hora de SQL Server."
        )

    return fecha_hora

def guardar_novedad_bitacora(
    idturno: int,
    fecha_hora: datetime,
    id_tipo_novedad: int,
    id_buque: int,
    id_registro: int,
    sc_registro: int | None,
    detalle: str,
) -> int | None:
    """Registra una novedad mediante dbo.SPJ_Insert_Bitacora."""

    rows = execute_procedure(
        "dbo.SPJ_Insert_Bitacora",
        (
            ("@idturno", idturno),
            ("@fechaHora", fecha_hora),
            ("@idTipoNovedad", id_tipo_novedad),
            ("@idBuque", id_buque),
            ("@idRegistro", id_registro),
            ("@scRegistro", sc_registro),
            ("@detalle", detalle),
        ),
        commit=True,
    )

    if not rows:
        return None

    nuevo_id = rows[0].get("newid")

    return int(nuevo_id) if nuevo_id is not None else None


def obtener_historial_turno(idturno: int) -> list[dict]:
    rows = execute_query(
        "EXEC dbo.SPJ_ReporteBitacoraTurno ?",
        (idturno,),
    )

    historial = []

    for row in rows:
        tipo_novedad = str(
            row.get("tiponovedad") or "Novedad"
        ).strip()

        detalle = str(
            row.get("detalle") or ""
        ).strip()

        # ======================================================
        # REPORTES
        # ======================================================
        if detalle.upper().startswith("[REPORTE]"):
            tipo_novedad = "Reportes"
            detalle = detalle[len("[REPORTE]"):].strip()

        # ======================================================
        # CONSIGNAS
        # ======================================================
        elif detalle.upper().startswith("[CONSIGNA]"):
            tipo_novedad = "Consignas"
            detalle = detalle[len("[CONSIGNA]"):].strip()

        historial.append(
            {
                "hora": str(row.get("hora") or ""),
                "buque_novedad": tipo_novedad,
                "detalle": detalle,
                "fecha_hora": row.get("fechahora"),
            }
        )

    return historial

def obtener_turnos_con_novedades() -> list[dict]:
    """
    Obtiene todos los turnos de bitácora que poseen
    al menos una novedad registrada.

    Incluye turnos abiertos y finalizados de todos
    los inspectores.
    """

    return execute_query(
        """
        SELECT DISTINCT
            t.idturno,
            t.idusuario,
            t.nombre,
            t.usuario,
            t.fecha_i,
            t.fecha_s,
            t.cargo
        FROM dbo.dim_mov_bitacora AS b

        INNER JOIN dbo.dim_con_mov_turno AS t
            ON t.idturno = b.idturno

        WHERE b.idestado = 1
          AND t.bitacora = 1

        ORDER BY t.fecha_i ASC
        """
    )


def obtener_bitacora_completa() -> list[dict]:
    """
    Construye la bitácora completa agrupando las novedades
    por turno e inspector.
    """

    turnos = obtener_turnos_con_novedades()

    bitacora = []

    for turno in turnos:
        idturno = turno.get("idturno")

        if idturno is None:
            continue

        novedades = obtener_historial_turno(
            int(idturno)
        )

        # Solo mostrar turnos que realmente tengan novedades.
        if not novedades:
            continue

        bitacora.append(
            {
                "idturno": idturno,
                "idusuario": turno.get("idusuario"),
                "nombre": turno.get("nombre") or "",
                "usuario": turno.get("usuario") or "",
                "cargo": turno.get("cargo") or "",
                "fecha_inicio": turno.get("fecha_i"),
                "fecha_fin": turno.get("fecha_s"),
                "novedades": novedades,
            }
        )

    return bitacora