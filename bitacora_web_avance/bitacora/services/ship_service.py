"""Servicios para consulta de buques."""

from __future__ import annotations

from typing import Any

from django.conf import settings

from .db_connection import (
    execute_query,
    format_datetime,
    first_value,
)


def _normalize_ship_rows(
    rows: list[dict[str, Any]],
    tipo: str,
) -> list[dict[str, Any]]:
    """Normaliza filas de buques al contrato esperado por la interfaz."""

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
                    ("idregistro", "registro_id", "sgregistro", "scregistro"),
                ),
            }
        )

    return ships


def obtener_buques_industriales() -> list[dict[str, Any]]:
    """Obtiene los buques industriales que permanecen activos."""

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

    rows = execute_query(
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

    return _normalize_ship_rows(
        rows,
        "industrial",
    )


def obtener_buques_artesanales() -> list[dict[str, Any]]:
    """Obtiene los buques artesanales que permanecen activos."""

    if settings.DEMO_MODE:
        return []

    rows = execute_query(
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

    return _normalize_ship_rows(
        rows,
        "artesanal",
    )