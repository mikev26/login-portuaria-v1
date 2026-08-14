"""Servicios de conexión y utilidades de base de datos."""

from __future__ import annotations

import os
import re
from contextlib import closing
from datetime import date, datetime
from typing import Any, Iterable

try:
    import pyodbc
except ImportError:
    pyodbc = None


class DatabaseConfigurationError(RuntimeError):
    """Falta configuración necesaria para acceder a SQL Server."""


class DatabaseContractError(RuntimeError):
    """El procedimiento no devolvió el contrato esperado por Django."""


_IDENTIFIER_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*(\.[A-Za-z_][A-Za-z0-9_]*){1,2}$")
_PARAMETER_RE = re.compile(r"^@[A-Za-z_][A-Za-z0-9_]*$")


def _connection_string(database_name: str | None = None) -> str:
    driver = os.getenv("DB_DRIVER", "ODBC Driver 18 for SQL Server").strip()
    server = os.getenv("DB_SERVER", "").strip()
    port = os.getenv("DB_PORT", "1433").strip()
    database = (database_name or os.getenv("DB_NAME", "dim_sis_puerto_v1")).strip()
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


def get_connection(database_name: str | None = None):
    if pyodbc is None:
        raise DatabaseConfigurationError(
            "pyodbc no está instalado. Ejecuta: pip install -r requirements.txt"
        )
    return pyodbc.connect(_connection_string(database_name))


def _rows_as_dicts(cursor) -> list[dict[str, Any]]:
    if cursor.description is None:
        return []
    columns = [column[0].lower() for column in cursor.description]
    return [dict(zip(columns, row)) for row in cursor.fetchall()]


def execute_procedure(
    procedure: str,
    parameters: Iterable[tuple[str, Any]] = (),
) -> list[dict[str, Any]]:
    """Ejecuta un procedimiento almacenado y devuelve resultados como lista de dicts."""
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


def validated_procedure(env_name: str, required: bool = True) -> str:
    """Valida y obtiene nombre de procedimiento desde variable de entorno."""
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


def validated_parameter(env_name: str, default: str) -> str:
    """Valida y obtiene nombre de parámetro desde variable de entorno."""
    value = os.getenv(env_name, default).strip()
    if not _PARAMETER_RE.fullmatch(value):
        raise DatabaseConfigurationError(
            f"{env_name} debe ser un nombre de parámetro como @usuario."
        )
    return value


def bool_value(value: Any) -> bool:
    """Convierte un valor a booleano siguiendo reglas de negocio."""
    if value is None:
        return False
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return value != 0
    return str(value).strip().lower() in {
        "1", "true", "si", "sí", "ok", "autorizado", "valido", "válido"
    }


def first_value(row: dict[str, Any], keys: Iterable[str], default: Any = None) -> Any:
    """Retorna el primer valor no-nulo de un diccionario para las claves dadas."""
    for key in keys:
        if key in row and row[key] is not None:
            return row[key]
    return default


def format_datetime(value: Any) -> str:
    """Formatea un valor de fecha/hora al formato dd/mm/yyyy HH:MM."""
    if value is None:
        return ""
    if isinstance(value, datetime):
        return value.strftime("%d/%m/%Y %H:%M")
    if isinstance(value, date):
        return value.strftime("%d/%m/%Y")
    return str(value)


def is_missing_object_error(exc: Exception) -> bool:
    """Detecta si la excepción es por procedimiento/vista no encontrado."""
    if pyodbc is None or not isinstance(exc, pyodbc.ProgrammingError):
        return False
    message = str(exc).lower()
    return "2812" in message or "no se encontró el procedimiento almacenado" in message
