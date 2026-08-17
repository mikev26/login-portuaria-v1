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
    )

    if not rows:
        return None

    nuevo_id = rows[0].get("newid")

    return int(nuevo_id) if nuevo_id is not None else None


def obtener_historial_turno(idturno: int) -> list[dict]:
    """Obtiene las novedades registradas para un turno."""

    rows = execute_query(
        """
        SELECT
            b.fechaHora AS fecha_hora,
            b.idTipoNovedad AS id_tipo_novedad,
            b.detalle,

            CASE
                WHEN b.idTipoNovedad = 1
                    THEN COALESCE(i.buque, 'Buque industrial')

                WHEN b.idTipoNovedad = 2
                    THEN COALESCE(a.buque, 'Buque artesanal')

                ELSE 'Novedad'
            END AS buque_novedad

        FROM dbo.dim_mov_bitacora AS b

        LEFT JOIN dbo.dim_con_maestro_registro_lista AS i
            ON b.idTipoNovedad = 1
           AND i.idbuque = b.idBuque
           AND i.idregistro = b.idRegistro

        LEFT JOIN dbo.dim_con_maestro_registro_cabotaje AS a
            ON b.idTipoNovedad = 2
           AND a.idbuque = b.idBuque
           AND a.scregistro = b.idRegistro

        WHERE b.idturno = ?
          AND b.idestado = 1

        ORDER BY b.fechaHora DESC
        """,
        (idturno,),
    )

    historial = []

    for row in rows:
        fecha_hora = row.get("fecha_hora")

        if isinstance(fecha_hora, datetime):
            hora = fecha_hora.strftime("%H:%M")
        else:
            hora = str(fecha_hora or "")

        historial.append(
            {
                "hora": hora,
                "buque_novedad": row.get("buque_novedad") or "Novedad",
                "detalle": row.get("detalle") or "",
            }
        )

    return historial