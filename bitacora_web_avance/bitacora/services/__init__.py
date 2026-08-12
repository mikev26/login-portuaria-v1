"""Servicios de negocio separados por dominio."""

from .auth_service import validar_usuario, obtener_turnos_usuario
from .ship_service import (
    obtener_buques_industriales,
    obtener_buques_artesanales,
    obtener_historial_turno,
)
from .report_service import obtener_reporte_inec
from .combustible import obtener_reporte_combustible
from .db_connection import (
    DatabaseConfigurationError,
    DatabaseContractError,
    get_connection,
)

__all__ = [
    "validar_usuario",
    "obtener_turnos_usuario",
    "obtener_buques_industriales",
    "obtener_buques_artesanales",
    "obtener_reporte_inec",
    "obtener_reporte_combustible",
    "DatabaseConfigurationError",
    "DatabaseContractError",
    "get_connection",
]
