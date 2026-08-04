"""Acceso a SQL Server exclusivamente mediante procedimientos almacenados."""

from __future__ import annotations

import os
import re
from contextlib import closing
from datetime import date, datetime
from typing import Any, Iterable

from django.conf import settings

try:
    import pyodbc
except ImportError:  # Permite abrir el proyecto antes de instalar requirements.
    pyodbc = None


class DatabaseConfigurationError(RuntimeError):
    """Falta configuración necesaria para acceder a SQL Server."""


class DatabaseContractError(RuntimeError):
    """El procedimiento no devolvió el contrato esperado por Django."""


_IDENTIFIER_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*(\.[A-Za-z_][A-Za-z0-9_]*){1,2}$")
_PARAMETER_RE = re.compile(r"^@[A-Za-z_][A-Za-z0-9_]*$")


def _validated_procedure(env_name: str, required: bool = True) -> str:
    value = os.getenv(env_name, "").strip()
    if not value:
        if required:
            raise DatabaseConfigurationError(
                f"Falta configurar {env_name} en el archivo .env."
            )
        return ""

    if not _IDENTIFIER_RE.fullmatch(value):
        raise DatabaseConfigurationError(
            f"{env_name} debe tener formato esquema.procedimiento "
            "o base.esquema.procedimiento."
        )
    return value


def _validated_parameter(env_name: str, default: str) -> str:
    value = os.getenv(env_name, default).strip()
    if not _PARAMETER_RE.fullmatch(value):
        raise DatabaseConfigurationError(
            f"{env_name} debe ser un nombre de parámetro como @usuario."
        )
    return value


def _connection_string() -> str:
    driver = os.getenv("DB_DRIVER", "ODBC Driver 18 for SQL Server").strip()
    server = os.getenv("DB_SERVER", "").strip()
    port = os.getenv("DB_PORT", "1433").strip()
    database = os.getenv("DB_NAME", "dim_sis_puerto_v1").strip()
    trusted = os.getenv("DB_TRUSTED_CONNECTION", "no").strip().lower() in {
        "1", "true", "yes", "si", "sí", "on"
    }

    if not server:
        raise DatabaseConfigurationError("Falta DB_SERVER en el archivo .env.")
    if not database:
        raise DatabaseConfigurationError("Falta DB_NAME en el archivo .env.")

    server_value = server if not port else f"{server},{port}"
    parts = [
        f"DRIVER={{{driver}}}",
        f"SERVER={server_value}",
        f"DATABASE={database}",
    ]

    if trusted:
        parts.append("Trusted_Connection=yes")
    else:
        user = os.getenv("DB_USER", "").strip()
        password = os.getenv("DB_PASSWORD", "")
        if not user or not password:
            raise DatabaseConfigurationError(
                "Faltan DB_USER o DB_PASSWORD en el archivo .env."
            )
        parts.extend([f"UID={user}", f"PWD={password}"])

    parts.extend(
        [
            f"Encrypt={os.getenv('DB_ENCRYPT', 'no')}",
            f"TrustServerCertificate={os.getenv('DB_TRUST_SERVER_CERTIFICATE', 'yes')}",
            f"Connection Timeout={os.getenv('DB_TIMEOUT', '8')}",
        ]
    )
    return ";".join(parts) + ";"


def get_connection():
    if pyodbc is None:
        raise DatabaseConfigurationError(
            "pyodbc no está instalado. Ejecuta: pip install -r requirements.txt"
        )
    return pyodbc.connect(_connection_string())


def _rows_as_dicts(cursor) -> list[dict[str, Any]]:
    if cursor.description is None:
        return []
    columns = [column[0].lower() for column in cursor.description]
    return [dict(zip(columns, row)) for row in cursor.fetchall()]


def _execute_procedure(
    procedure: str,
    parameters: Iterable[tuple[str, Any]] = (),
) -> list[dict[str, Any]]:
    params = list(parameters)
    assignments = ", ".join(f"{name}=?" for name, _ in params)
    sql = f"EXEC {procedure} {assignments}" if assignments else f"EXEC {procedure}"
    values = [value for _, value in params]

    with closing(get_connection()) as connection:
        with closing(connection.cursor()) as cursor:
            if values:
                cursor.execute(sql, *values)
            else:
                cursor.execute(sql)

            # Algunos procedimientos primero emiten resultados auxiliares.
            while cursor.description is None and cursor.nextset():
                pass

            return _rows_as_dicts(cursor)


def _bool_value(value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return value != 0
    return str(value).strip().lower() in {
        "1", "true", "si", "sí", "ok", "autorizado", "valido", "válido"
    }


def _first_value(row: dict[str, Any], keys: Iterable[str], default: Any = None) -> Any:
    for key in keys:
        if key in row and row[key] is not None:
            return row[key]
    return default


def _format_datetime(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, datetime):
        return value.strftime("%d/%m/%Y %H:%M")
    if isinstance(value, date):
        return value.strftime("%d/%m/%Y")
    return str(value)


def validar_usuario(usuario: str, clave: str) -> dict[str, Any] | None:
    """
    Valida las credenciales con el procedimiento institucional existente.

    Contrato mínimo esperado del primer registro:
    - idusuario (o usuario_id / idfuncionario)
    - nombre (opcional)
    - usuario (opcional)
    - autorizado / valido / resultado (opcional; si no existe, una fila implica éxito)
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

    procedure = _validated_procedure("SP_LOGIN")
    user_param = _validated_parameter("SP_LOGIN_USER_PARAM", "@usuario")
    password_param = _validated_parameter("SP_LOGIN_PASSWORD_PARAM", "@clave")

    rows = _execute_procedure(
        procedure,
        [(user_param, usuario), (password_param, clave)],
    )
    if not rows:
        return None

    row = rows[0]
    status_keys = ("autorizado", "valido", "válido", "resultado", "estado_login")
    present_status = next((key for key in status_keys if key in row), None)
    if present_status and not _bool_value(row[present_status]):
        return None

    idusuario = _first_value(row, ("idusuario", "usuario_id", "idfuncionario", "id"))
    if idusuario is None:
        raise DatabaseContractError(
            "El procedimiento de login respondió, pero no devolvió idusuario."
        )

    return {
        "idusuario": idusuario,
        "usuario": _first_value(row, ("usuario", "login", "username"), usuario),
        "nombre": _first_value(row, ("nombre", "nombre_completo", "funcionario"), usuario),
        "cargo": _first_value(row, ("cargo", "rol", "perfil"), "Inspector"),
    }


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

    procedure = _validated_procedure("SP_TURNOS_ACTIVOS")
    id_param = _validated_parameter("SP_TURNOS_ID_PARAM", "@idusuario")
    rows = _execute_procedure(procedure, [(id_param, idusuario)])

    turnos = []
    for row in rows:
        turnos.append(
            {
                "idturno": _first_value(row, ("idturno", "turno_id")),
                "idusuario": _first_value(row, ("idusuario", "usuario_id"), idusuario),
                "fecha_inicio": _format_datetime(
                    _first_value(row, ("fecha_i", "fecha_inicio", "inicia_turno"))
                ),
                "fecha_fin": _format_datetime(
                    _first_value(row, ("fecha_s", "fecha_fin", "finaliza_turno"))
                ),
                "nombre": _first_value(row, ("nombre", "funcionario"), ""),
                "usuario": _first_value(row, ("usuario", "login"), ""),
                "numero": _first_value(row, ("numero", "identificacion"), ""),
                "cargo": _first_value(row, ("cargo", "rol"), ""),
                # Pendiente de enlazar al procedimiento real del historial.
                "novedades": [],
            }
        )
    return turnos


def _normalize_ship_rows(rows: list[dict[str, Any]], tipo: str) -> list[dict[str, Any]]:
    ships = []
    for row in rows:
        ships.append(
            {
                "tipo": tipo,
                "scbuque": _first_value(row, ("scbuque", "sgregistro", "codigo"), ""),
                "nombre": _first_value(row, ("nombre", "buque"), "Sin nombre"),
                "matricula": _first_value(row, ("n_matricula", "matricula"), ""),
                "fecha_arribo": _format_datetime(
                    _first_value(row, ("fecha_arrivo", "fecha_arribo", "fecha_ing"))
                ),
                "cabo": _first_value(row, ("cabo",), 0),
                "idbuque": _first_value(row, ("idbuque", "buque_id")),
                "idregistro": _first_value(row, ("idregistro", "registro_id", "sgregistro")),
            }
        )
    return ships


def obtener_buques_industriales() -> list[dict[str, Any]]:
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

    procedure = _validated_procedure("SP_BUQUES_INDUSTRIALES")
    return _normalize_ship_rows(_execute_procedure(procedure), "industrial")


def obtener_buques_artesanales() -> list[dict[str, Any]]:
    if settings.DEMO_MODE:
        return []

    procedure = _validated_procedure("SP_BUQUES_ARTESANALES")
    return _normalize_ship_rows(_execute_procedure(procedure), "artesanal")
