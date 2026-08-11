"""Servicios para generación de reportes."""

from __future__ import annotations

import os
from datetime import date
from typing import Any

from .db_connection import (
    DatabaseConfigurationError,
    _IDENTIFIER_RE,
    _PARAMETER_RE,
    execute_procedure,
)


def obtener_reporte_inec(fecha_inicio: date, fecha_fin: date) -> list[dict[str, Any]]:
    if fecha_inicio > fecha_fin:
        fecha_inicio, fecha_fin = fecha_fin, fecha_inicio

    procedure = os.getenv("SPJ_REPORTE_INEC", "dbo.SPJ_REPORTE_INEC").strip()
    fechainit_param = os.getenv("SPJ_REPORTE_INEC_FECHAINIT_PARAM", "@s_fechaInit").strip()
    fechafin_param = os.getenv("SPJ_REPORTE_INEC_FECHAFIN_PARAM", "@s_fechaFin").strip()

    if not _IDENTIFIER_RE.fullmatch(procedure):
        raise DatabaseConfigurationError("SPJ_REPORTE_INEC debe tener formato esquema.procedimiento")

    fechainit_param = fechainit_param if fechainit_param.startswith("@") else f"@{fechainit_param}"
    fechafin_param = fechafin_param if fechafin_param.startswith("@") else f"@{fechafin_param}"

    if not _PARAMETER_RE.fullmatch(fechainit_param):
        raise DatabaseConfigurationError(
            "SPJ_REPORTE_INEC_FECHAINIT_PARAM debe ser un nombre de parámetro válido"
        )
    if not _PARAMETER_RE.fullmatch(fechafin_param):
        raise DatabaseConfigurationError(
            "SPJ_REPORTE_INEC_FECHAFIN_PARAM debe ser un nombre de parámetro válido"
        )

    return execute_procedure(
        procedure,
        [
            (fechainit_param, fecha_inicio),
            (fechafin_param, fecha_fin),
        ],
    )
