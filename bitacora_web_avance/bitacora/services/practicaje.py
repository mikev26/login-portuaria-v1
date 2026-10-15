"""Acceso a los datos del módulo de practicaje."""

from __future__ import annotations

from datetime import date
from typing import Any

from .db_connection import execute_procedure


PRACTICAJE_PROCEDURE = "dbo.SPJ_DatosPracticaje"


def obtener_datos_practicaje(
    fecha_inicio: date,
    fecha_fin: date,
) -> list[dict[str, Any]]:
    """Obtiene los datos de practicaje para un rango de fechas."""
    filas = execute_procedure(
        PRACTICAJE_PROCEDURE,
        (
            ("@s_fechaInit", fecha_inicio),
            ("@s_fechaFin", fecha_fin),
        ),
    )
    registros = []
    for nro, fila in enumerate(filas, start=1):
        valores = {str(clave).lower(): valor for clave, valor in fila.items()}
        registros.append(
            {
                "nro": nro,
                "registro": valores.get("registro", ""),
                "buque": valores.get("buque", ""),
                "bandera": valores.get("bandera", ""),
                "ipb": valores.get("ipb", ""),
                "ano": valores.get("ano", ""),
                "ubicacion": valores.get("ubicacion", ""),
                "usuario": valores.get("usuario", ""),
                "operadora": valores.get("operadora", ""),
                "tipomaniobra": valores.get("tipomaniobra", ""),
                "trimestre": valores.get("trimestre", ""),
                "fecha": valores.get("fecha", ""),
            }
        )
    return registros
