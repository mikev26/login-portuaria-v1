from __future__ import annotations

from typing import Any

from .db_connection import (
    DatabaseConfigurationError,
    DatabaseContractError,
    _IDENTIFIER_RE,
    execute_procedure,
)


DATOS_ABIERTOS_FIELD_MAP = (
    ("REGISTRO", "Registro"),
    ("CODBUQUE", "CodBuque"),
    ("MATRÍCULA", "Matrícula"),
    ("BUQUE", "Buque"),
    ("TipoNave", "Tipo de Nave"),
    ("Arribo", "Arribo"),
    ("Zarpe", "Zarpe"),
    ("Bandera", "Bandera"),
    ("TRB", "TRB"),
    ("TRN", "TRN"),
    ("Agencia", "Agencia"),
    ("TotalDescarga", "Total Descarga"),
)


def _coerce_row_value(row: dict[str, Any], *keys: str) -> Any:
    for key in keys:
        if key in row and row[key] is not None:
            return row[key]

    normalized = {str(k).lower(): v for k, v in row.items()}
    for key in keys:
        normalized_key = str(key).lower()
        if normalized_key in normalized and normalized[normalized_key] is not None:
            return normalized[normalized_key]
    return None


def _map_datos_abiertos_row(row: dict[str, Any]) -> dict[str, Any]:
    mapped: dict[str, Any] = {}
    for source_key, target_key in DATOS_ABIERTOS_FIELD_MAP:
        value = _coerce_row_value(
            row,
            source_key,
            source_key.lower(),
            source_key.replace(" ", "_"),
            source_key.replace("-", "_"),
        )
        mapped[target_key] = value

        safe_key = target_key.replace(" ", "").replace("-", "")
        mapped[safe_key] = value

        if " " in target_key:
            mapped[target_key.replace(" ", "_")] = value

        if "Tipo de Nave" == target_key:
            mapped["TipoNave"] = value
        if "Total Descarga" == target_key:
            mapped["TotalDescarga"] = value

    return mapped


def obtener_reporte_datos_abiertos(
    anio: int,
    semestre: str | int,
) -> list[dict[str, Any]]:
    """Ejecución del SP dbo.SPJ_DatosAbiertosTPyC y mapeo de 12 columnas."""

    procedure_candidates = [
        "dbo.SPJ_DatosAbiertosTPyC",
        "dbo.SP_DatosAbiertosTPyC",
    ]

    semestre_valor = semestre
    if isinstance(semestre_valor, str):
        semestre_normalizado = str(semestre_valor or "").strip().lower()
        if semestre_normalizado in {"1er", "1"}:
            semestre_valor = 1
        elif semestre_normalizado in {"2do", "2"}:
            semestre_valor = 2
        else:
            raise DatabaseContractError(
                "El semestre debe ser '1er' o '2do' para datos abiertos."
            )

    semestre_numero = int(semestre_valor)
    if semestre_numero not in {1, 2}:
        raise DatabaseContractError(
            "El semestre debe ser '1er' o '2do' para datos abiertos."
        )

    procedure_params = {
        "dbo.SPJ_DatosAbiertosTPyC": (
            ("@sPeriodo", int(anio)),
            ("@sSemestre", semestre_numero),
        ),
        "dbo.SP_DatosAbiertosTPyC": (
            ("@sPeriodo", int(anio)),
            ("@sSemestre", semestre_numero),
        ),
    }

    last_error: Exception | None = None
    for procedure in procedure_candidates:
        if not _IDENTIFIER_RE.fullmatch(procedure):
            continue
        try:
            rows = execute_procedure(procedure, procedure_params[procedure])
            return [_map_datos_abiertos_row(row) for row in rows]
        except Exception as exc:  # pragma: no cover - compatibility fallback
            last_error = exc

    if last_error is not None:
        raise last_error

    raise DatabaseConfigurationError(
        "El procedimiento configurado para datos abiertos no tiene un formato válido."
    )
