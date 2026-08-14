import os
from datetime import date
from typing import Any, Iterable
from contextlib import closing

from django.conf import settings


from .db_connection import (
    DatabaseConfigurationError,
    _IDENTIFIER_RE,
    _PARAMETER_RE,
    _rows_as_dicts,
    execute_procedure,
    get_connection,
)


def _execute_query(
    sql: str,
    parameters: Iterable[Any] = (),
) -> list[dict[str, Any]]:
    with closing(get_connection()) as connection:
        with closing(connection.cursor()) as cursor:
            cursor.execute(sql, *parameters)
            return _rows_as_dicts(cursor)


def _query_columns(
    sql: str,
    parameters: Iterable[Any] = (),
) -> list[str]:
    with closing(get_connection()) as connection:
        with closing(connection.cursor()) as cursor:
            cursor.execute(sql, *parameters)

            if cursor.description is None:
                return []

            return [
                column[0].lower()
                for column in cursor.description
            ]


def _find_date_column(
    columns: list[str],
) -> str | None:
    candidates = [
        "fecha",
        "fecha_registro",
        "fecha_mov",
        "fecha_ing",
        "fecha_ingresa",
        "fecha_salida",
        "fecha_documento",
        "fregistro",
        "f_registro",
        "f_mov",
    ]

    for candidate in candidates:
        if candidate in columns:
            return candidate

    for column in columns:
        column_lower = column.lower()

        if (
            "fecha" in column_lower
            or column_lower.startswith("f")
        ):
            return column

    return None


def obtener_registros_combustible(
    fecha_inicio: date | None = None,
    fecha_fin: date | None = None,
) -> list[dict[str, Any]]:
    """
    Obtiene registros de combustible directamente
    desde la tabla configurada.
    """

    if settings.DEMO_MODE:
        return [
            {
                "registro": 1,
                "fecha": "05/08/2026",
                "producto": "Gasolina",
                "cantidad_litros": 1250,
                "terminal": "Manta",
            },
            {
                "registro": 2,
                "fecha": "04/08/2026",
                "producto": "Diésel",
                "cantidad_litros": 1920,
                "terminal": "Manta",
            },
        ]

    source = os.getenv(
        "COMBUSTIBLE_TABLE",
        "dbo.dimm_con_maestro_registro_combust",
    ).strip()

    if not _IDENTIFIER_RE.fullmatch(source):
        raise DatabaseConfigurationError(
            "COMBUSTIBLE_TABLE debe tener formato "
            "esquema.objeto o base.esquema.objeto."
        )

    date_column = _find_date_column(
        _query_columns(
            f"SELECT TOP 0 * FROM {source}"
        )
    )

    where_clauses: list[str] = []
    params: list[Any] = []

    if date_column is not None:

        if fecha_inicio is not None:
            where_clauses.append(
                f"{date_column} >= ?"
            )
            params.append(fecha_inicio)

        if fecha_fin is not None:
            where_clauses.append(
                f"{date_column} <= ?"
            )
            params.append(fecha_fin)

    sql = f"SELECT * FROM {source}"

    if where_clauses:
        sql += " WHERE " + " AND ".join(where_clauses)

    sql += " ORDER BY 1"

    return _execute_query(sql, params)


def obtener_reporte_combustible(
    fecha_inicio: date,
    fecha_fin: date,
) -> list[dict[str, Any]]:
    """
    Ejecuta el procedimiento almacenado
    utilizado por el reporte de combustible.
    """

    if settings.DEMO_MODE:
        return [
            {
                "registro": 1,
                "fecha": "05/08/2026",
                "producto": "Gasolina",
                "cantidad_litros": 1250,
                "terminal": "Manta",
            },
            {
                "registro": 2,
                "fecha": "04/08/2026",
                "producto": "Diésel",
                "cantidad_litros": 1920,
                "terminal": "Manta",
            },
        ]

    procedure = "dbo.SPJ_ReporteCombustible"

    if not _IDENTIFIER_RE.fullmatch(procedure):
        raise DatabaseConfigurationError(
            "El procedimiento configurado para el "
            "reporte no tiene un formato válido."
        )

    return execute_procedure(
        procedure,
        (
            ("@s_fechaInit", fecha_inicio),
            ("@s_fechaFin", fecha_fin),
        ),
    )