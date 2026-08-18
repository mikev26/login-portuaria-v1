"""Servicios de negocio separados por dominio."""

from .auth_service import validar_usuario, obtener_turnos_usuario
from .ship_service import obtener_buques_industriales, obtener_buques_artesanales
from .report_service import obtener_reporte_inec
from .tarifario import (obtener_tarifas_existentes, obtener_partidas, obtener_tasa_por_id, obtener_siguiente_codigo_tarifa, guardar_tarifa, anular_tarifa,)
from .combustible import obtener_reporte_combustible
from .reporte_buque import ( obtener_catalogos_reporte_buques, obtener_datos_reporte_buques,)
from .reporte_buque_excel import (exportar_reporte_buques_excel)
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
    "obtener_catalogos_reporte_buques",
    "obtener_datos_reporte_buques",
    "exportar_reporte_buques_excel",
    "DatabaseConfigurationError",
    "DatabaseContractError",
    "get_connection",
    "obtener_tarifas_existentes",
    "obtener_partidas",
    "obtener_tasa_por_id",
    "obtener_siguiente_codigo_tarifa",
    "guardar_tarifa",
    "anular_tarifa",
]
