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


def _is_missing_object_error(exc: Exception) -> bool:
    if pyodbc is None or not isinstance(exc, pyodbc.ProgrammingError):
        return False
    message = str(exc).lower()
    return "2812" in message or "no se encontró el procedimiento almacenado" in message


def _login_desde_vista_turno(usuario: str, clave: str) -> dict[str, Any] | None:
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

    try:
        procedure = _validated_procedure("SP_BUQUES_INDUSTRIALES")
        return _normalize_ship_rows(_execute_procedure(procedure), "industrial")
    except Exception as exc:
        if _is_missing_object_error(exc):
            return []
        raise


def obtener_buques_artesanales() -> list[dict[str, Any]]:
    if settings.DEMO_MODE:
        return []

    try:
        procedure = _validated_procedure("SP_BUQUES_ARTESANALES")
        return _normalize_ship_rows(_execute_procedure(procedure), "artesanal")
    except Exception as exc:
        if _is_missing_object_error(exc):
            return []
        raise


def obtener_reporte_inec(fecha_inicio: date, fecha_fin: date) -> list[dict[str, Any]]:
    """Obtiene el reporte INEC llamando al procedimiento por año y filtrando por rango.

    El procedimiento debe aceptar un parámetro año. El nombre del procedimiento y
    del parámetro se configura en las variables de entorno `SP_REPORTE_INEC` y
    `SP_REPORTE_INEC_ANIO_PARAM`.
    """
    if fecha_inicio > fecha_fin:
        fecha_inicio, fecha_fin = fecha_fin, fecha_inicio

    procedure = os.getenv("SP_REPORTE_INEC", "dbo.SP_Reporte_INEC").strip()
    anio_param = os.getenv("SP_REPORTE_INEC_ANIO_PARAM", "@anio").strip()

    if not _IDENTIFIER_RE.fullmatch(procedure):
        raise DatabaseConfigurationError("SP_REPORTE_INEC debe tener formato esquema.procedimiento")

    resultados: list[dict[str, Any]] = []
    # Intentar llamar al procedimiento por año. Si el SP informa que espera
    # otro nombre de parámetro (por ejemplo '@s_ano'), lo extraemos del
    # mensaje de error y reintentamos con ese nombre.
    missing_param_re = re.compile(r"['\"](@[A-Za-z0-9_]+)['\"]")
    for anio in range(fecha_inicio.year, fecha_fin.year + 1):
        try:
            rows = _execute_procedure(procedure, [(anio_param, anio)])
        except Exception as exc:
            # Si falta el procedimiento, continuar con el siguiente año.
            if _is_missing_object_error(exc):
                continue

            # Detectar error de parámetro faltante y reintentar con el nombre
            # de parámetro que apareció en el mensaje (p.ej. '@s_ano').
            msg = str(exc)
            if pyodbc is not None and isinstance(exc, pyodbc.ProgrammingError):
                lower = msg.lower()
                if "esperaba el parámetro" in lower or "expected parameter" in lower:
                    m = missing_param_re.search(msg)
                    if m:
                        nuevo_param = m.group(1)
                        if _PARAMETER_RE.fullmatch(nuevo_param):
                            anio_param = nuevo_param
                            # reintentar la misma iteración con el nuevo nombre
                            rows = _execute_procedure(procedure, [(anio_param, anio)])
                        else:
                            raise DatabaseConfigurationError(
                                "Nombre de parámetro inesperado en SP_REPORTE_INEC_ANIO_PARAM"
                            ) from exc
                    else:
                        raise
                else:
                    raise
            else:
                raise

        for row in rows:
            resultados.append(row)

    # Intentar detectar la columna de fecha para filtrar
    date_key = None
    if resultados:
        keys = list(resultados[0].keys())
        for k in keys:
            if "fecha" in k or "date" in k or "dia" in k:
                date_key = k
                break

    def _to_date(val: Any) -> date | None:
        if val is None:
            return None
        if isinstance(val, datetime):
            return val.date()
        if isinstance(val, date):
            return val
        s = str(val).strip()
        for fmt in ("%d/%m/%Y %H:%M", "%d/%m/%Y", "%Y-%m-%d", "%Y/%m/%d"):
            try:
                return datetime.strptime(s, fmt).date()
            except Exception:
                continue
        return None

    if date_key:
        filtrados: list[dict[str, Any]] = []
        for row in resultados:
            d = _to_date(row.get(date_key))
            if d is None:
                continue
            if fecha_inicio <= d <= fecha_fin:
                filtrados.append(row)
        return filtrados

    return resultados
