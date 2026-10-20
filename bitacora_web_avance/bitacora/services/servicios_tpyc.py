"""
Servicio para la gestión de Servicios TPyC.
"""
from __future__ import annotations

import logging
from contextlib import closing
from decimal import Decimal
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
                try:
                    cursor.execute("EXEC dbo.SPJ_consultas_servicios")
                except Exception as sp_exc:
                    if is_missing_object_error(sp_exc):
                        cursor.execute("EXEC dbo.SPJ_v_servicios")
                    else:
                        raise
                rows = _rows_as_dicts(cursor)
                return rows
    except Exception as exc:
        if is_missing_object_error(exc):
            logger.warning("El procedimiento almacenado de servicios no existe aún en la base de datos.")
            return []
        logger.exception("Error al ejecutar procedimiento de servicios")
        return []


def obtener_tarifas_activas_tpyc() -> list[dict[str, Any]]:
    """
    Ejecuta el procedimiento almacenado dbo.SPJ_v_tarifas con @estado = 1
    para obtener las tarifas activas utilizadas en Servicios TPyC.
    """
    if getattr(settings, "DEMO_MODE", False):
        return [
            {
                "sctarifa": "117",
                "tarifa": "USO DE FACILIDADES DE ACCESO DE BUQUES",
                "idtasa": 5,
                "activo": 1,
            },
            {
                "sctarifa": "339",
                "tarifa": "PRACTICAJE Y MANIOBRAS ESPECIALES",
                "idtasa": 7,
                "activo": 1,
            },
            {
                "sctarifa": "247",
                "tarifa": "USO DE FACILIDADES DE ACCESO DE BUQUES",
                "idtasa": 2,
                "activo": 1,
            },
        ]

    try:
        with closing(get_connection()) as connection:
            with closing(connection.cursor()) as cursor:
                cursor.execute("EXEC dbo.SPJ_v_tarifas @estado = 1")
                rows = _rows_as_dicts(cursor)
                for r in rows:
                    for k, v in list(r.items()):
                        if isinstance(v, Decimal):
                            r[k] = str(v)
                return rows
    except Exception as exc:
        if is_missing_object_error(exc):
            logger.warning("El procedimiento almacenado dbo.SPJ_v_tarifas no existe aún en la base de datos.")
            return []
        logger.exception("Error al ejecutar dbo.SPJ_v_tarifas en Servicios TPyC")
        return []


def obtener_grupos_servicio() -> list[dict[str, Any]]:
    """
    Obtiene el listado de grupos de servicio válidos desde dbo.GrupoServicio.
    """
    if getattr(settings, "DEMO_MODE", False):
        return [
            {"id": 2, "gruposer": "Cant"},
            {"id": 3, "gruposer": "CARG"},
            {"id": 4, "gruposer": "CARGA"},
            {"id": 5, "gruposer": "GRUA"},
            {"id": 6, "gruposer": "MANIO"},
            {"id": 7, "gruposer": "O.Espacio"},
            {"id": 8, "gruposer": "OTROS"},
            {"id": 9, "gruposer": "PRAC"},
            {"id": 10, "gruposer": "REMOL"},
            {"id": 1, "gruposer": "S/G"},
        ]

    try:
        with closing(get_connection()) as connection:
            with closing(connection.cursor()) as cursor:
                cursor.execute("SELECT id, gruposer FROM dbo.GrupoServicio ORDER BY gruposer ASC")
                return _rows_as_dicts(cursor)
    except Exception as exc:
        logger.exception("Error al consultar dbo.GrupoServicio")
        return []


def obtener_medidas_servicio() -> list[dict[str, Any]]:
    """
    Obtiene el listado de medidas válidas desde dbo.Medida.
    """
    if getattr(settings, "DEMO_MODE", False):
        return [
            {"id": 1, "medida": "Cant"},
            {"id": 2, "medida": "Dias"},
            {"id": 3, "medida": "Dias_D"},
            {"id": 4, "medida": "Eslora-Manga_D"},
            {"id": 5, "medida": "Eslora-Manga_H"},
            {"id": 6, "medida": "Horas"},
            {"id": 7, "medida": "M.Cuadrados_D"},
            {"id": 8, "medida": "M.Cuadrados_H"},
            {"id": 9, "medida": "M.Cubicos_D"},
            {"id": 10, "medida": "M.Cubicos_H"},
            {"id": 11, "medida": "TN"},
            {"id": 12, "medida": "Ton"},
            {"id": 13, "medida": "Unidad_D"},
        ]

    try:
        with closing(get_connection()) as connection:
            with closing(connection.cursor()) as cursor:
                cursor.execute("SELECT id, medida FROM dbo.Medida ORDER BY medida ASC")
                return _rows_as_dicts(cursor)
    except Exception as exc:
        logger.exception("Error al consultar dbo.Medida")
        return []


def insertar_servicio_tpyc(
    servicio: str,
    medida: str,
    grupo: str,
    detalle: str = "",
    t_n: int = 0,
    t_e: int = 0,
    t_i: int = 0,
    cidtarifa: int = 0,
    eidtarifa: int = 0,
    nidtarifa: int = 0,
    civa: int = 0,
) -> dict[str, Any]:
    """
    Inserta un nuevo servicio ejecutando dbo.SPJ_Insert_Servicios.
    Retorna {'success': bool, 'idservicio': int, 'mensaje': str}.
    """
    if getattr(settings, "DEMO_MODE", False):
        return {
            "success": True,
            "idservicio": 9999,
            "mensaje": "Servicio registrado correctamente (Modo Demostración).",
        }

    servicio_limpio = (servicio or "").strip()
    if not servicio_limpio:
        return {"success": False, "idservicio": 0, "mensaje": "El nombre del servicio es obligatorio."}

    sql = """
    DECLARE @resul INT;
    EXEC dbo.SPJ_Insert_Servicios
        @sservicio = ?,
        @smedida = ?,
        @sgrupo = ?,
        @sdetalle = ?,
        @st_n = ?,
        @st_e = ?,
        @scidtarifa = ?,
        @seidtarifa = ?,
        @sciva = ?,
        @st_i = ?,
        @snidtarifa = ?,
        @sresul = @resul OUTPUT;
    SELECT @resul AS id_generado;
    """

    params = (
        servicio_limpio,
        (medida or "").strip(),
        (grupo or "").strip(),
        str(detalle or "").strip()[:50],
        int(t_n),
        int(t_e),
        int(cidtarifa or 0),
        int(eidtarifa or 0),
        int(civa or 0),
        int(t_i),
        int(nidtarifa or 0),
    )

    try:
        with closing(get_connection()) as connection:
            with closing(connection.cursor()) as cursor:
                cursor.execute(sql, params)
                row = cursor.fetchone()
                id_generado = int(row[0]) if row and row[0] is not None else 0
                connection.commit()

                return {
                    "success": True,
                    "idservicio": id_generado,
                    "mensaje": "Servicio registrado exitosamente.",
                }
    except Exception as exc:
        msg = str(exc)
        logger.exception("Error al insertar servicio TPyC: %s", msg)
        # Extraer mensaje si es THROW de SQL Server
        if "El servicio ya se encuentra registrado" in msg:
            return {"success": False, "idservicio": 0, "mensaje": "El servicio ya se encuentra registrado."}
        if "El nombre del servicio es obligatorio" in msg:
            return {"success": False, "idservicio": 0, "mensaje": "El nombre del servicio es obligatorio."}
        return {"success": False, "idservicio": 0, "mensaje": f"Error al guardar: {msg}"}


def actualizar_servicio_tpyc(
    idservicio: int,
    servicio: str,
    medida: str,
    grupo: str,
    detalle: str = "",
    t_n: int = 0,
    t_e: int = 0,
    t_i: int = 0,
    cidtarifa: int = 0,
    eidtarifa: int = 0,
    nidtarifa: int = 0,
) -> dict[str, Any]:
    """
    Actualiza un servicio existente ejecutando dbo.SPJ_Update_Servicios.
    Retorna {'success': bool, 'idservicio': int, 'mensaje': str}.
    """
    if getattr(settings, "DEMO_MODE", False):
        return {
            "success": True,
            "idservicio": idservicio,
            "mensaje": "Servicio actualizado correctamente (Modo Demostración).",
        }

    if not idservicio or int(idservicio) <= 0:
        return {"success": False, "idservicio": 0, "mensaje": "El ID del servicio es inválido."}

    servicio_limpio = (servicio or "").strip()
    if not servicio_limpio:
        return {"success": False, "idservicio": idservicio, "mensaje": "El nombre del servicio es obligatorio."}

    sql = """
    DECLARE @resul INT;
    EXEC dbo.SPJ_Update_Servicios
        @sidservicio = ?,
        @sservicio = ?,
        @smedida = ?,
        @sgrupo = ?,
        @sdetalle = ?,
        @st_n = ?,
        @st_e = ?,
        @scidtarifa = ?,
        @seidtarifa = ?,
        @st_i = ?,
        @snidtarifa = ?,
        @sresul = @resul OUTPUT;
    SELECT @resul AS id_actualizado;
    """

    params = (
        int(idservicio),
        servicio_limpio,
        (medida or "").strip(),
        (grupo or "").strip(),
        str(detalle or "").strip()[:50],
        int(t_n),
        int(t_e),
        int(cidtarifa or 0),
        int(eidtarifa or 0),
        int(t_i),
        int(nidtarifa or 0),
    )

    try:
        with closing(get_connection()) as connection:
            with closing(connection.cursor()) as cursor:
                cursor.execute(sql, params)
                row = cursor.fetchone()
                id_actualizado = int(row[0]) if row and row[0] is not None else idservicio
                connection.commit()

                return {
                    "success": True,
                    "idservicio": id_actualizado,
                    "mensaje": "Servicio actualizado exitosamente.",
                }
    except Exception as exc:
        msg = str(exc)
        logger.exception("Error al actualizar servicio TPyC: %s", msg)
        if "Ya existe otro servicio registrado con ese mismo nombre" in msg:
            return {"success": False, "idservicio": idservicio, "mensaje": "Ya existe otro servicio registrado con ese mismo nombre."}
        if "El servicio a actualizar no existe" in msg:
            return {"success": False, "idservicio": idservicio, "mensaje": "El servicio no existe en la base de datos."}
        return {"success": False, "idservicio": idservicio, "mensaje": f"Error al actualizar: {msg}"}



