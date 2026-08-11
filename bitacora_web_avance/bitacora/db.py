"""Acceso a SQL Server exclusivamente mediante procedimientos almacenados."""

from __future__ import annotations

import os
import re
import json
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

def obtener_partidas(codigo: str | int = 1) -> list[dict[str, Any]]:
    """
    Realiza una consulta directa a la tabla dbo.dim_partida.
    """
    if settings.DEMO_MODE:
        mock_partidas = [
            {
                "idpartida": 1,
                "codigo": "170202",
                "partidafinanzas": "Rentas por Arrendamientos de Bienes",
                "scpartida": "17.02.02.00.",
                "activo": 1,
            },
            {
                "idpartida": 2,
                "codigo": "1302010100",
                "partidafinanzas": "ACCESO AL PUERTO MARITIMO",
                "scpartida": "13.02.01.01.00.",
                "activo": 1,
            },
            {
                "idpartida": 3,
                "codigo": "1302010400",
                "partidafinanzas": "PRACTICAJE",
                "scpartida": "13.02.01.04.00.",
                "activo": 1,
            },
            {
                "idpartida": 4,
                "codigo": "1401020300",
                "partidafinanzas": "SERVICIOS LOGISTICOS PORTUARIOS",
                "scpartida": "14.01.02.03.00.",
                "activo": 1,
            },
            {
                "idpartida": 5,
                "codigo": "1402050100",
                "partidafinanzas": "ALMACENAMIENTO TEMPORAL",
                "scpartida": "14.02.05.01.00.",
                "activo": 1,
            }
        ]
        codigo_str = str(codigo).strip().lower()
        if not codigo_str:
            return mock_partidas
        return [
            p for p in mock_partidas
            if (codigo_str in p["scpartida"].lower() or 
                codigo_str in p["codigo"].lower() or 
                codigo_str in p["partidafinanzas"].lower())
        ]

    try:
        with closing(get_connection()) as connection:
            with closing(connection.cursor()) as cursor:
                cursor.execute(
                    """
                    SELECT 
                        idpartida,
                        cedulaFinanza AS codigo,
                        nombreFinanza AS partidafinanzas,
                        scpartida,
                        activo
                    FROM dbo.dim_partida
                    WHERE (scpartida LIKE ? OR cedulaFinanza LIKE ?)
                      AND activo = 1
                    """,
                    str(codigo) + "%",
                    str(codigo) + "%",
                )
                rows = _rows_as_dicts(cursor)
                return rows
    except Exception as exc:
        if _is_missing_object_error(exc):
            return []
        raise


def obtener_tasa_por_id(idtasa: int | str = "") -> list[dict[str, Any]]:
    """
    Realiza una consulta directa a la tabla dbo.dim_tasa.
    """
    if settings.DEMO_MODE:
        tasa_map = {
            "5": "TASA CABOTAJE",
            "7": "TASAS ESPECIFICAS",
            "2": "TASAS A LAS NAVES",
        }
        if not idtasa:
            return [{"idtasa": int(k), "tasa": v} for k, v in tasa_map.items()]
        
        idtasa_str = str(idtasa).strip().lower()
        return [
            {"idtasa": int(k), "tasa": v}
            for k, v in tasa_map.items()
            if idtasa_str in k or idtasa_str in v.lower()
        ]

    try:
        with closing(get_connection()) as connection:
            with closing(connection.cursor()) as cursor:
                if idtasa:
                    cursor.execute(
                        """
                        SELECT 
                            idtasa,
                            tasa
                        FROM dbo.dim_tasa
                        WHERE idtasa = ? OR tasa LIKE ?
                        """,
                        int(idtasa) if str(idtasa).isdigit() else idtasa,
                        "%" + str(idtasa) + "%",
                    )
                else:
                    cursor.execute(
                        """
                        SELECT 
                            idtasa,
                            tasa
                        FROM dbo.dim_tasa
                        """
                    )
                rows = _rows_as_dicts(cursor)
                return rows
    except Exception as exc:
        if _is_missing_object_error(exc):
            return []
        raise


def obtener_siguiente_codigo_tarifa(idtasa: int | str) -> int:
    """
    Calcula el siguiente código secuencial para las tarifas asociadas a una tasa
    utilizando el procedimiento almacenado dbo.SPJ_Vista_TasasTarifas.
    """
    if settings.DEMO_MODE:
        tasa_next_map = {
            "5": 118,
            "2": 248,
            "7": 340,
        }
        return tasa_next_map.get(str(idtasa), 1)

    try:
        try:
            idtasa_int = int(idtasa)
        except (ValueError, TypeError):
            idtasa_int = 0

        with closing(get_connection()) as connection:
            with closing(connection.cursor()) as cursor:
                cursor.execute(
                    """
                    DECLARE @out INT;
                    EXEC dbo.SPJ_Vista_TasasTarifas @SidTasa = ?, @SidResulta = @out OUTPUT;
                    SELECT @out AS siguiente;
                    """,
                    idtasa_int,
                )
                row = cursor.fetchone()
                if row and row[0] is not None:
                    return row[0]
                
                # Códigos base si no retorna nada
                base_codes = {
                    "5": 101,
                    "2": 201,
                    "7": 301,
                }
                return base_codes.get(str(idtasa), 1)
    except Exception:
        # Fallback si falla la base de datos o no existe el SP aún
        tasa_next_map = {
            "5": 118,
            "2": 248,
            "7": 340,
        }
        return tasa_next_map.get(str(idtasa), 1)


def obtener_tarifas_existentes() -> list[dict[str, Any]]:
    """
    Ejecuta el procedimiento almacenado sp_v_tarifas 1 para obtener el listado de tarifas.
    """
    if settings.DEMO_MODE:
        normalized = [
            {
                "id": "1",
                "codigo": "117",
                "activa": True,
                "tasa": "TASA CABOTAJE",
                "tasa_id": "5",
                "tarifa": "USO DE FACILIDADES DE ACCESO DE BUQUES",
                "partida_cod": "17.02.02.00.",
                "partida_desc": "Rentas por Arrendamientos de Bienes",
                "partida_cedula": "170202",
                "formula": "(Eslora * 1.25) * Dia",
                "detalle": "Tarifa regulada para barcos pesqueros y de cabotaje",
                "valor": "0.13",
                "s_ante": "10",
                "se_cobra_iva": False,
                "senae_cod": "S-99",
                "senae_desc": "Regulación nacional de cabotaje",
                "calc_param": "eslora",
                "calc_unidad": "dia",
                "ticket_srv": "ninguno"
            },
            {
                "id": "2",
                "codigo": "247",
                "activa": True,
                "tasa": "TASAS A LAS NAVES",
                "tasa_id": "2",
                "tarifa": "USO DE FACILIDADES DE ACCESO DE BUQUES",
                "partida_cod": "13.02.01.01.00.",
                "partida_desc": "ACCESO AL PUERTO MARITIMO",
                "partida_cedula": "1302010100",
                "formula": "(T.Neto * 2.50) * Horas",
                "detalle": "Tarifa portuaria naves mercantes internacionales",
                "valor": "0.50",
                "s_ante": "15",
                "se_cobra_iva": True,
                "senae_cod": "S-102",
                "senae_desc": "Impuestos aduaneros generales",
                "calc_param": "t_neto",
                "calc_unidad": "horas",
                "ticket_srv": "muelle"
            },
            {
                "id": "3",
                "codigo": "339",
                "activa": False,
                "tasa": "TASAS ESPECIFICAS",
                "tasa_id": "7",
                "tarifa": "USO DE FACILIDADES DE ACCESO DE BUQUES",
                "partida_cod": "13.02.01.04.00.",
                "partida_desc": "PRACTICAJE",
                "partida_cedula": "1302010400",
                "formula": "Cantidad * 0.85",
                "detalle": "Cobro por servicios específicos y especiales",
                "valor": "1.00",
                "s_ante": "20",
                "se_cobra_iva": True,
                "senae_cod": "S-205",
                "senae_desc": "Tarifación aduanera específica",
                "calc_param": "otros",
                "calc_unidad": "cantidad",
                "ticket_srv": "vehiculo"
            }
        ]
        for t in normalized:
            t["json_data"] = json.dumps(t)
        return normalized

    try:
        with closing(get_connection()) as connection:
            with closing(connection.cursor()) as cursor:
                cursor.execute("EXEC dbo.sp_v_tarifas 1")
                rows = _rows_as_dicts(cursor)
                
                normalized = []
                for r in rows:
                    def str_or_empty(val: Any, default: str = "") -> str:
                        if val is None or str(val).strip().lower() == "none":
                            return default
                        return str(val).strip()

                    t_val = {
                        "id": str_or_empty(_first_value(r, ["idtarifa", "id", "id_tarifa"])),
                        "codigo": str_or_empty(_first_value(r, ["codigo", "cod_tarifa", "cod"])),
                        "activa": _bool_value(_first_value(r, ["activa", "activo", "estado"], True)),
                        "tasa": str_or_empty(_first_value(r, ["tasa", "tasa_desc", "nombre_tasa"])),
                        "tasa_id": str_or_empty(_first_value(r, ["tasa_id", "idtasa", "id_tasa"])),
                        "tarifa": str_or_empty(_first_value(r, ["tarifa", "nombre", "descripcion", "tarifa_desc"])),
                        "partida_cod": str_or_empty(_first_value(r, ["partida_cod", "scpartida", "partida"])),
                        "partida_desc": str_or_empty(_first_value(r, ["partida_desc", "nombreFinanza", "partidafinanzas"])),
                        "partida_cedula": str_or_empty(_first_value(r, ["partida_cedula", "cedulaFinanza", "cedula"])),
                        "formula": str_or_empty(_first_value(r, ["formula", "formula_calc"])),
                        "detalle": str_or_empty(_first_value(r, ["detalle", "especificacion", "obs", "observacion"])),
                        "valor": str_or_empty(_first_value(r, ["valor", "monto", "precio"], "0.00")),
                        "s_ante": str_or_empty(_first_value(r, ["s_ante", "s_antecedente", "id_ante"])),
                        "se_cobra_iva": _bool_value(_first_value(r, ["se_cobra_iva", "iva", "cobra_iva", "cobrar_iva"], False)),
                        "senae_cod": str_or_empty(_first_value(r, ["senae_cod", "codigo_senae", "senae"])),
                        "senae_desc": str_or_empty(_first_value(r, ["senae_desc", "detalle_senae"])),
                        "calc_param": str_or_empty(_first_value(r, ["calc_param", "parametro", "param_principal"], "eslora")),
                        "calc_unidad": str_or_empty(_first_value(r, ["calc_unidad", "unidad", "unidad_cobro"], "dia")),
                        "ticket_srv": str_or_empty(_first_value(r, ["ticket_srv", "servicio", "servicio_vinculado"], "ninguno")),
                    }
                    t_val["json_data"] = json.dumps(t_val)
                    normalized.append(t_val)
                return normalized
    except Exception as exc:
        if _is_missing_object_error(exc):
            return []
        raise