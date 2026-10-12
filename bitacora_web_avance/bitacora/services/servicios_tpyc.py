"""
Servicio para la gestión de Servicios TPyC.
"""
from __future__ import annotations

import logging
from contextlib import closing
from typing import Any

from django.conf import settings

from .db_connection import (
    get_connection,
    _rows_as_dicts,
    is_missing_object_error,
)

logger = logging.getLogger(__name__)


def obtener_servicios_tpyc() -> list[dict[str, Any]]:
    """
    Ejecuta el procedimiento almacenado dbo.SPJ_v_servicios para obtener
    el listado de servicios TPyC.
    """
    if getattr(settings, "DEMO_MODE", False):
        return [
            {
                "idservicio": 52,
                "servicio": "ABARLOAMIENTO MUELLE AGUAS PROFUND",
                "idgrupo": 7,
                "grupo": "SERVICIOS PORTUARIOS",
                "idmedida": 3,
                "medida": "DIA",
                "valor": None,
            },
            {
                "idservicio": 53,
                "servicio": "ALMACENAMIENTO DE CONTENEDORES",
                "idgrupo": 10,
                "grupo": "ALMACENAJE",
                "idmedida": 1,
                "medida": "UNIDAD",
                "valor": None,
            },
            {
                "idservicio": 54,
                "servicio": "USO DE FACILIDADES PORTUARIAS",
                "idgrupo": 9,
                "grupo": "OPERACIONES",
                "idmedida": 1,
                "medida": "UNIDAD",
                "valor": None,
            }
        ]

    try:
        with closing(get_connection()) as connection:
            with closing(connection.cursor()) as cursor:
                cursor.execute("EXEC dbo.SPJ_v_servicios")
                rows = _rows_as_dicts(cursor)
                return rows
    except Exception as exc:
        if is_missing_object_error(exc):
            logger.warning("El procedimiento almacenado dbo.SPJ_v_servicios no existe aún en la base de datos.")
            return []
        logger.exception("Error al ejecutar dbo.SPJ_v_servicios")
        return []
