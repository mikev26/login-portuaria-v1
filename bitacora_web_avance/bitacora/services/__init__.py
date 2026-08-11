"""Servicios de negocio separados por dominio."""

from .auth_service import validar_usuario, obtener_turnos_usuario
from .ship_service import obtener_buques_industriales, obtener_buques_artesanales
from .report_service import obtener_reporte_inec
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
    "DatabaseConfigurationError",
    "DatabaseContractError",
    "get_connection",
]
