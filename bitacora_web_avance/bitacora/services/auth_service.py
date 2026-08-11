"""Servicios de autenticación y validación de usuarios."""

from __future__ import annotations

import os
from contextlib import closing
from typing import Any

from django.conf import settings

from .db_connection import (
    DatabaseConfigurationError,
    _rows_as_dicts,
    _IDENTIFIER_RE,
    execute_procedure,
    get_connection,
    format_datetime,
    first_value,
    is_missing_object_error,
)

try:
    import pyodbc
except ImportError:
    pyodbc = None


def _login_desde_vista_turno(usuario: str, clave: str) -> dict[str, Any] | None:
    """Autentica usuario consultando la vista de turnos activos."""
    login_view = os.getenv("LOGIN_VIEW", "dbo.dim_con_mov_turno").strip()
    if not _IDENTIFIER_RE.fullmatch(login_view):
        raise DatabaseConfigurationError(
            "LOGIN_VIEW debe tener formato esquema.vista o base.esquema.vista."
        )

    with closing(get_connection()) as connection:
        with closing(connection.cursor()) as cursor:
            cursor.execute(
                f"""
                SELECT TOP 1 idusuario, usuario, nombre, cargo
                FROM {login_view}
                WHERE usuario = ?
                  AND ClaveBitacora = ?
                  AND fecha_s IS NULL
                  AND activo <> 7
                  AND bitacora = 1
                ORDER BY idturno DESC, idusuario
                """,
                usuario,
                clave,
            )
            row = cursor.fetchone()

    if row is None:
        return None

    return {
        "idusuario": row[0],
        "usuario": row[1],
        "nombre": row[2],
        "cargo": row[3] or "Inspector",
    }


def validar_usuario(usuario: str, clave: str) -> dict[str, Any] | None:
    """
    Valida las credenciales con la vista de turnos activa.

    Contrato mínimo esperado del primer registro:
    - idusuario
    - usuario
    - nombre (opcional)
    - cargo (opcional)
    """
    if settings.DEMO_MODE:
        if usuario == "inspector.demo" and clave == "Demo1234":
            return {
                "idusuario": 4,
                "usuario": "inspector.demo",
                "nombre": "Inspector de demostración",
                "cargo": "Inspector del Terminal Pesquero y Cabotaje",
            }
        return None

    try:
        return _login_desde_vista_turno(usuario, clave)
    except Exception as exc:
        if pyodbc is not None and isinstance(exc, pyodbc.ProgrammingError):
            message = str(exc).lower()
            if "no se encontró la vista" in message or "invalid object name" in message:
                raise DatabaseConfigurationError(
                    "No se encontró la vista LOGIN_VIEW configurada para el login."
                ) from exc
        raise


def obtener_turnos_usuario(idusuario: int) -> list[dict[str, Any]]:
    """Devuelve los turnos activos autorizados para la bitácora."""
    if settings.DEMO_MODE:
        return [
            {
                "idturno": 643,
                "idusuario": idusuario,
                "fecha_inicio": "31/07/2026 08:00",
                "fecha_fin": "",
                "nombre": "Inspector de demostración",
                "usuario": "inspector.demo",
                "numero": "17461",
                "cargo": "Inspector del Terminal Pesquero y Cabotaje",
                "novedades": [],
            }
        ]

    login_view = os.getenv("LOGIN_VIEW", "dbo.dim_con_mov_turno").strip()
    if not _IDENTIFIER_RE.fullmatch(login_view):
        raise DatabaseConfigurationError(
            "LOGIN_VIEW debe tener formato esquema.vista o base.esquema.vista."
        )

    with closing(get_connection()) as connection:
        with closing(connection.cursor()) as cursor:
            cursor.execute(
                f"""
                SELECT idturno, idusuario, fecha_i, fecha_s, nombre, usuario, numero, cargo
                FROM {login_view}
                WHERE fecha_s IS NULL
                  AND activo <> 7
                  AND bitacora = 1
                  AND idusuario = ?
                ORDER BY idturno DESC
                """,
                idusuario,
            )
            rows = _rows_as_dicts(cursor)

    turnos = []
    for row in rows:
        turnos.append(
            {
                "idturno": first_value(row, ("idturno", "turno_id")),
                "idusuario": first_value(row, ("idusuario", "usuario_id"), idusuario),
                "fecha_inicio": format_datetime(
                    first_value(row, ("fecha_i", "fecha_inicio", "inicia_turno"))
                ),
                "fecha_fin": format_datetime(
                    first_value(row, ("fecha_s", "fecha_fin", "finaliza_turno"))
                ),
                "nombre": first_value(row, ("nombre", "funcionario"), ""),
                "usuario": first_value(row, ("usuario", "login"), ""),
                "numero": first_value(row, ("numero", "identificacion"), ""),
                "cargo": first_value(row, ("cargo", "rol"), ""),
                "novedades": [],
            }
        )
    return turnos
