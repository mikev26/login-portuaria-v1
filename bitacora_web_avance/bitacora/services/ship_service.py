"""Servicios para consulta de buques."""

from __future__ import annotations

from contextlib import closing
from typing import Any

from django.conf import settings

from .db_connection import (
    _rows_as_dicts,
    execute_procedure,
    format_datetime,
    first_value,
    get_connection,
    is_missing_object_error,
    validated_procedure,
)


def _normalize_ship_rows(
    rows: list[dict[str, Any]],
    tipo: str,
) -> list[dict[str, Any]]:
    """Normaliza filas de buques al contrato esperado."""

    ships = []

    for row in rows:
        ships.append(
            {
                "tipo": tipo,
                "scbuque": first_value(
                    row,
                    ("scbuque", "sgregistro", "scregistro", "codigo"),
                    "",
                ),
                "nombre": first_value(
                    row,
                    ("nombre", "buque"),
                    "Sin nombre",
                ),
                "matricula": first_value(
                    row,
                    ("n_matricula", "matricula"),
                    "",
                ),
                "fecha_arribo": format_datetime(
                    first_value(
                        row,
                        ("fecha_arrivo", "fecha_arribo", "fecha_ing"),
                    )
                ),
                "cabo": first_value(
                    row,
                    ("cabo",),
                    0,
                ),
                "idbuque": first_value(
                    row,
                    ("idbuque", "buque_id"),
                ),
                "idregistro": first_value(
                    row,
                    ("idregistro", "registro_id", "sgregistro"),
                ),
            }
        )

    return ships


# ============================================================
# BUQUES INDUSTRIALES
# ============================================================

def obtener_buques_industriales() -> list[dict[str, Any]]:
    """Obtiene lista de buques industriales activos."""

    if settings.DEMO_MODE:
        return _normalize_ship_rows(
            [
                {
                    "scbuque": 20250427,
                    "nombre": "CARONI II",
                    "n_matricula": "APNN-PE-0319",
                    "fecha_arrivo": "16/07/2025 21:40",
                    "cabo": 0,
                    "idbuque": 2742,
                    "idregistro": 36676,
                },
                {
                    "scbuque": 20250425,
                    "nombre": "ALDO",
                    "n_matricula": "P-04-00870",
                    "fecha_arrivo": "15/07/2025 18:00",
                    "cabo": 0,
                    "idbuque": 3006,
                    "idregistro": 36674,
                },
            ],
            "industrial",
        )

    with closing(get_connection()) as connection:
        with closing(connection.cursor()) as cursor:
            cursor.execute(
                """
                SELECT
                    scregistro AS scbuque,
                    buque AS nombre,
                    n_matricula,
                    fecha_arrivo,
                    0 AS cabo,
                    idbuque,
                    idregistro
                FROM dbo.dim_con_maestro_registro_lista
                WHERE fecha_zarpe IS NULL
                  AND idestado <> 7
                ORDER BY buque
                """
            )

            rows = _rows_as_dicts(cursor)

    return _normalize_ship_rows(rows, "industrial")


# ============================================================
# BUQUES ARTESANALES
# ============================================================

def obtener_buques_artesanales() -> list[dict[str, Any]]:
    """Obtiene lista de buques artesanales activos."""

    if settings.DEMO_MODE:
        return []

    with closing(get_connection()) as connection:
        with closing(connection.cursor()) as cursor:
            cursor.execute(
                """
                SELECT
                    scregistro AS scbuque,
                    buque AS nombre,
                    n_matricula,
                    fecha_ing AS fecha_arrivo,
                    0 AS cabo,
                    idbuque,
                    scregistro AS idregistro
                FROM dbo.dim_con_maestro_registro_cabotaje
                WHERE fecha_salida IS NULL
                  AND idestado <> 7
                ORDER BY buque
                """
            )

            rows = _rows_as_dicts(cursor)

    return _normalize_ship_rows(rows, "artesanal")


# ============================================================
# HISTORIAL DE NOVEDADES DEL TURNO
# ============================================================

def obtener_historial_turno(idturno: int) -> list[dict[str, Any]]:
    """
    Obtiene las novedades que pertenecen al turno indicado.

    Solo muestra registros realizados dentro del horario real
    del turno, evitando incluir novedades anteriores al inicio.
    """

    if settings.DEMO_MODE:
        return []

    with closing(get_connection()) as connection:
        with closing(connection.cursor()) as cursor:
            cursor.execute(
                """
                WITH turno_actual AS (
                    SELECT TOP 1
                        fecha_i,
                        fecha_s
                    FROM dbo.dim_con_mov_turno
                    WHERE idturno = ?
                    ORDER BY fecha_i DESC
                )

                SELECT
                    e.fecha_i,
                    e.idregistro,
                    e.idbuque,
                    e.tipo,

                    CASE
                        WHEN e.tipo = 1 THEN industrial.buque
                        WHEN e.tipo = 3 THEN artesanal.buque
                        ELSE NULL
                    END AS buque,

                    e.obser

                FROM dbo.dim_maestro_registro_maniobras_espacio e

                CROSS JOIN turno_actual t

                OUTER APPLY (
                    SELECT TOP 1
                        i.buque
                    FROM dbo.dim_con_maestro_registro_lista i
                    WHERE i.idregistro = e.idregistro
                      AND i.idbuque = e.idbuque
                    ORDER BY i.scregistro DESC
                ) industrial

                OUTER APPLY (
                    SELECT TOP 1
                        a.buque
                    FROM dbo.dim_con_maestro_registro_cabotaje a
                    WHERE a.idbuque = e.idbuque
                    ORDER BY a.scregistro DESC
                ) artesanal

                WHERE e.idturno_i = ?
                  AND e.fecha_i >= t.fecha_i
                  AND (
                        t.fecha_s IS NULL
                        OR e.fecha_i <= t.fecha_s
                      )

                ORDER BY e.fecha_i DESC
                """,
                idturno,
                idturno,
            )

            rows = _rows_as_dicts(cursor)

    historial = []

    for row in rows:
        fecha = row.get("fecha_i")

        historial.append(
            {
                "hora": (
                    fecha.strftime("%H:%M")
                    if fecha
                    else ""
                ),
                "buque_novedad": (
                    row.get("buque")
                    or "Sin buque"
                ),
                "detalle": (
                    row.get("obser")
                    or ""
                ),
            }
        )

    return historial