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
    get_connection,
    format_datetime,
    first_value,
)

try:
    import pyodbc
except ImportError:
    pyodbc = None


def _leer_resultado_procedimiento(cursor) -> list[dict[str, Any]]:
    """
    Lee el primer conjunto de resultados NO vacío devuelto por un SP.

    SPJ_ValidarUserAcceso puede devolver:
    - datos del usuario cuando es válido;
    - idusuario = 0 cuando no hay coincidencia.
    """
    while True:
        if cursor.description is not None:
            columnas = [columna[0] for columna in cursor.description]
            filas = cursor.fetchall()

            if filas:
                return [
                    {
                        columnas[indice]: fila[indice]
                        for indice in range(len(columnas))
                    }
                    for fila in filas
                ]

        if not cursor.nextset():
            break

    return []


def _resultado_es_valido(rows: list[dict[str, Any]]) -> bool:
    """Devuelve True si el SP devolvió un idusuario distinto de 0."""
    if not rows:
        return False

    for row in rows:
        idusuario = first_value(
            row,
            ("idusuario", "usuario_id"),
        )

        if idusuario in (None, "", 0, "0"):
            continue

        try:
            if int(idusuario) > 0:
                return True
        except (TypeError, ValueError):
            continue

    return False


def _fila_usuario_valida(
    rows: list[dict[str, Any]],
) -> dict[str, Any] | None:
    """Obtiene la primera fila válida devuelta por el procedimiento."""
    for row in rows:
        idusuario = first_value(
            row,
            ("idusuario", "usuario_id"),
        )

        if idusuario in (None, "", 0, "0"):
            continue

        try:
            if int(idusuario) > 0:
                return row
        except (TypeError, ValueError):
            continue

    return None


def _login_con_procedimiento(
    usuario: str,
    clave: str,
) -> dict[str, Any] | None:
    """
    Autentica usando el procedimiento configurado en AUTH_LOGIN_PROCEDURE.

    El password se envía en texto al SP. El procedimiento es quien aplica
    el HASH correspondiente en SQL Server.
    """
    auth_procedure = os.getenv(
        "AUTH_LOGIN_PROCEDURE",
        "op_claves.dbo.SPJ_ValidarUserAcceso",
    ).strip()

    login_view = os.getenv(
        "LOGIN_VIEW",
        "dbo.dim_UsuarioSistemas",
    ).strip()

    if not _IDENTIFIER_RE.fullmatch(auth_procedure):
        raise DatabaseConfigurationError(
            "AUTH_LOGIN_PROCEDURE debe tener formato "
            "esquema.procedimiento o base.esquema.procedimiento."
        )

    if not _IDENTIFIER_RE.fullmatch(login_view):
        raise DatabaseConfigurationError(
            "LOGIN_VIEW debe tener formato esquema.vista "
            "o base.esquema.vista."
        )

    with closing(get_connection()) as connection:
        with closing(connection.cursor()) as cursor:
            cursor.execute(
                f"EXEC {auth_procedure} ?, ?",
                usuario,
                clave,
            )

            rows = _leer_resultado_procedimiento(cursor)

    if not _resultado_es_valido(rows):
        return None

    fila_sp = _fila_usuario_valida(rows)

    if not fila_sp:
        return None

    idusuario = first_value(
        fila_sp,
        ("idusuario", "usuario_id"),
    )

    if idusuario in (None, "", 0, "0"):
        return None

    # Los datos visibles del sistema se toman desde dim_UsuarioSistemas.
    # Si hay varias filas históricas, se prioriza el turno abierto.
    with closing(get_connection()) as connection:
        with closing(connection.cursor()) as cursor:
            cursor.execute(
                f"""
                SELECT TOP 1
                    idusuario,
                    usuario,
                    nombre,
                    cargo
                FROM {login_view}
                WHERE idusuario = ?
                ORDER BY
                    CASE
                        WHEN fecha_i IS NOT NULL
                         AND fecha_s IS NULL
                         AND idturno IS NOT NULL
                        THEN 0
                        ELSE 1
                    END,
                    fecha_i DESC,
                    idturno DESC,
                    idusuario
                """,
                idusuario,
            )

            row = cursor.fetchone()

    if row is None:
        return None

    return {
        "idusuario": row[0],
        "usuario": row[1],
        "nombre": row[2],
        "cargo": row[3] or "Usuario",
    }


def validar_usuario(
    usuario: str,
    clave: str,
) -> dict[str, Any] | None:
    """Valida las credenciales del usuario."""
    usuario = (usuario or "").strip()

    if not usuario or not clave:
        return None

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
        return _login_con_procedimiento(
            usuario,
            clave,
        )

    except Exception as exc:
        if pyodbc is not None and isinstance(
            exc,
            pyodbc.ProgrammingError,
        ):
            message = str(exc).lower()

            if (
                "invalid object name" in message
                or "could not find stored procedure" in message
                or "no se encontró" in message
            ):
                raise DatabaseConfigurationError(
                    "No se encontró o no se pudo ejecutar la fuente "
                    "configurada para el login."
                ) from exc

        raise


def cambiar_contrasena_usuario(
    usuario: str,
    nueva_password: str,
) -> bool:
    """
    Envía al procedimiento únicamente:
        @usuario
        @password

    La contraseña de confirmación NO se envía a SQL Server.

    Después de ejecutar el procedimiento, se valida el acceso con la nueva
    contraseña para no informar éxito si SQL no la aceptó.
    """
    usuario = (usuario or "").strip()

    if not usuario or not nueva_password:
        return False

    if settings.DEMO_MODE:
        return False

    auth_procedure = os.getenv(
        "CHANGE_PASSWORD_PROCEDURE",
        "op_claves.dbo.SPJ_GenerarClaveBitacora",
    ).strip()

    if not _IDENTIFIER_RE.fullmatch(auth_procedure):
        raise DatabaseConfigurationError(
            "CHANGE_PASSWORD_PROCEDURE debe tener formato "
            "esquema.procedimiento o base.esquema.procedimiento."
        )

    with closing(get_connection()) as connection:
        with closing(connection.cursor()) as cursor:
            cursor.execute(
                f"""
                EXEC {auth_procedure}
                    @usuario = ?,
                    @password = ?
                """,
                usuario,
                nueva_password,
            )

            # Consumir todos los conjuntos de resultados del procedimiento.
            while True:
                if cursor.description is not None:
                    try:
                        cursor.fetchall()
                    except Exception:
                        pass

                if not cursor.nextset():
                    break

        connection.commit()

    # Verificación final: la nueva contraseña debe poder autenticar al usuario.
    usuario_validado = _login_con_procedimiento(
        usuario,
        nueva_password,
    )

    return usuario_validado is not None


def obtener_turnos_usuario(
    idusuario: int,
) -> list[dict[str, Any]]:
    """
    Devuelve únicamente los turnos abiertos del usuario.

    Regla de Bitácora:
        fecha_i IS NOT NULL
        fecha_s IS NULL
        idturno IS NOT NULL

    La antigüedad de fecha_i no invalida el turno.
    """
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

    login_view = os.getenv(
        "LOGIN_VIEW",
        "dbo.dim_UsuarioSistemas",
    ).strip()

    if not _IDENTIFIER_RE.fullmatch(login_view):
        raise DatabaseConfigurationError(
            "LOGIN_VIEW debe tener formato esquema.vista "
            "o base.esquema.vista."
        )

    with closing(get_connection()) as connection:
        with closing(connection.cursor()) as cursor:
            cursor.execute(
                f"""
                SELECT
                    idturno,
                    idusuario,
                    fecha_i,
                    fecha_s,
                    nombre,
                    usuario,
                    numero,
                    cargo
                FROM {login_view}
                WHERE idusuario = ?
                  AND fecha_i IS NOT NULL
                  AND fecha_s IS NULL
                  AND idturno IS NOT NULL
                ORDER BY
                    fecha_i DESC,
                    idturno DESC
                """,
                idusuario,
            )

            rows = _rows_as_dicts(cursor)

    turnos = []

    for row in rows:
        turnos.append(
            {
                "idturno": first_value(
                    row,
                    ("idturno", "turno_id"),
                ),
                "idusuario": first_value(
                    row,
                    ("idusuario", "usuario_id"),
                    idusuario,
                ),
                "fecha_inicio": format_datetime(
                    first_value(
                        row,
                        ("fecha_i", "fecha_inicio", "inicia_turno"),
                    )
                ),
                "fecha_fin": format_datetime(
                    first_value(
                        row,
                        ("fecha_s", "fecha_fin", "finaliza_turno"),
                    )
                ),
                "nombre": first_value(
                    row,
                    ("nombre", "funcionario"),
                    "",
                ),
                "usuario": first_value(
                    row,
                    ("usuario", "login"),
                    "",
                ),
                "numero": first_value(
                    row,
                    ("numero", "identificacion"),
                    "",
                ),
                "cargo": first_value(
                    row,
                    ("cargo", "rol"),
                    "",
                ),
                "novedades": [],
            }
        )

    return turnos
