"""Servicios para consulta de buques."""

from __future__ import annotations

from typing import Any

from django.conf import settings

from .db_connection import (
    execute_procedure,
    validated_procedure,
    format_datetime,
    first_value,
    is_missing_object_error,
)


def _normalize_ship_rows(rows: list[dict[str, Any]], tipo: str) -> list[dict[str, Any]]:
    """Normaliza filas de procedimiento de buques al contrato esperado."""
    ships = []
    for row in rows:
        ships.append(
            {
                "tipo": tipo,
                "scbuque": first_value(row, ("scbuque", "sgregistro", "codigo"), ""),
                "nombre": first_value(row, ("nombre", "buque"), "Sin nombre"),
                "matricula": first_value(row, ("n_matricula", "matricula"), ""),
                "fecha_arribo": format_datetime(
                    first_value(row, ("fecha_arrivo", "fecha_arribo", "fecha_ing"))
                ),
                "cabo": first_value(row, ("cabo",), 0),
                "idbuque": first_value(row, ("idbuque", "buque_id")),
                "idregistro": first_value(row, ("idregistro", "registro_id", "sgregistro")),
            }
        )
    return ships


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

    try:
        procedure = validated_procedure("SP_BUQUES_INDUSTRIALES")
        return _normalize_ship_rows(execute_procedure(procedure), "industrial")
    except Exception as exc:
        if is_missing_object_error(exc):
            return []
        raise


def obtener_buques_artesanales() -> list[dict[str, Any]]:
    """Obtiene lista de buques artesanales activos."""
    if settings.DEMO_MODE:
        return []

    try:
        procedure = validated_procedure("SP_BUQUES_ARTESANALES")
        return _normalize_ship_rows(execute_procedure(procedure), "artesanal")
    except Exception as exc:
        if is_missing_object_error(exc):
            return []
        raise
