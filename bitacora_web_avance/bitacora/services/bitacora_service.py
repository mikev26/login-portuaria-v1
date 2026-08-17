"""Servicios para registro e historial de la bitácora."""

from __future__ import annotations

from datetime import datetime

from .db_connection import execute_procedure, execute_query


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
    """
    Recupera las novedades registradas de un turno
    utilizando el procedimiento oficial
    dbo.SPJ_ReporteBitacoraTurno.
    """

    rows = execute_query(
        "EXEC dbo.SPJ_ReporteBitacoraTurno ?",
        (idturno,),
    )

    historial = []

    for row in rows:
        historial.append(
            {
                "hora": str(row.get("hora") or ""),
                "buque_novedad": row.get("tiponovedad") or "Novedad",
                "detalle": row.get("detalle") or "",
            }
        )

    return historial