
from __future__ import annotations

import json
from contextlib import closing
from typing import Any

from django.conf import settings

from .db import (
    get_connection,
    _rows_as_dicts,
    _bool_value,
    _first_value,
    _is_missing_object_error,
)




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
                "valor": "0.1300",
                "s_ante": "10",
                "se_cobra_iva": False,
                "senae_cod": "S-99",
                "senae_desc": "Regulación nacional de cabotaje",
                "calc_param": "eslora",
                "calc_unidad": "dia",
                "ticket_srv": "ninguno",
                "permitir_cambio_valor": False
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
                "valor": "0.5000",
                "s_ante": "15",
                "se_cobra_iva": True,
                "senae_cod": "S-102",
                "senae_desc": "Impuestos aduaneros generales",
                "calc_param": "t_neto",
                "calc_unidad": "horas",
                "ticket_srv": "muelle",
                "permitir_cambio_valor": False
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
                "valor": "1.0000",
                "s_ante": "20",
                "se_cobra_iva": True,
                "senae_cod": "S-205",
                "senae_desc": "Tarifación aduanera específica",
                "calc_param": "otros",
                "calc_unidad": "cantidad",
                "ticket_srv": "vehiculo",
                "permitir_cambio_valor": True
            }
        ]
        for t in normalized:
            t["json_data"] = json.dumps(t)
        return normalized

    try:
        tasa_map = {
            "5": "TASA CABOTAJE",
            "7": "TASAS ESPECIFICAS",
            "2": "TASAS A LAS NAVES",
        }
        with closing(get_connection()) as connection:
            with closing(connection.cursor()) as cursor:
                cursor.execute("EXEC dbo.SPJ_v_tarifas 1")
                rows = _rows_as_dicts(cursor)
                
                normalized = []
                for r in rows:
                    def str_or_empty(val: Any, default: str = "") -> str:
                        if val is None or str(val).strip().lower() == "none":
                            return default
                        return str(val).strip()

                    tasa_id_str = str_or_empty(_first_value(r, ["tasa_id", "idtasa", "id_tasa"]))
                    t_val = {
                        "id": str_or_empty(_first_value(r, ["idtarifa", "id", "id_tarifa"])),
                        "codigo": str_or_empty(_first_value(r, ["sctarifa", "codigo", "cod_tarifa", "cod"])),
                        "activa": _bool_value(_first_value(r, ["activa", "activo", "estado"], True)),
                        "tasa_id": tasa_id_str,
                        "tasa": tasa_map.get(tasa_id_str, ""),
                        "tarifa": str_or_empty(_first_value(r, ["tarifa", "nombre", "descripcion", "tarifa_desc"])),
                        "partida_cod": str_or_empty(_first_value(r, ["partida_cod", "scpartida", "partida"])),
                        "partida_desc": str_or_empty(_first_value(r, ["partida", "partida_desc", "nombrefinanza", "partidafinanzas"])),
                        "partida_cedula": str_or_empty(_first_value(r, ["cedulafinanza", "partida_cedula", "cedula"])),
                        "partida_id": str_or_empty(_first_value(r, ["idpartida", "partida_id"], "")),
                        "formula": str_or_empty(_first_value(r, ["formula", "formula_calc"])),
                        "detalle": str_or_empty(_first_value(r, ["detalle", "especificacion", "obs", "observacion"])),
                        "valor": str_or_empty(_first_value(r, ["valor", "monto", "precio"], "0.0000")),
                        "s_ante": str_or_empty(_first_value(r, ["s_ante", "s_antecedente", "id_ante"])),
                        "se_cobra_iva": _bool_value(_first_value(r, ["se_cobra_iva", "iva", "cobra_iva", "cobrar_iva"], False)),
                        "senae_cod": str_or_empty(_first_value(r, ["senae_cod", "codigo_senae", "senae"])),
                        "senae_desc": str_or_empty(_first_value(r, ["senae_desc", "detalle_senae"])),
                        "calc_param": "eslora" if _first_value(r, ["eslora_toneto"]) == 1 else ("t_neto" if _first_value(r, ["eslora_toneto"]) == 2 else "otros"),
                        "calc_unidad": "dia" if _first_value(r, ["dia_hora"]) == 1 else ("horas" if _first_value(r, ["dia_hora"]) == 2 else "cantidad"),
                        "ticket_srv": "vehiculo" if _first_value(r, ["tikect"]) == 1 else ("muelle" if _first_value(r, ["tikect"]) == 2 else "ninguno"),
                        "permitir_cambio_valor": _bool_value(_first_value(r, ["cambiofacturacion", "cambio_facturacion", "permitir_cambio_valor"], False)),
                    }
                    t_val["json_data"] = json.dumps(t_val)
                    normalized.append(t_val)
                return normalized
    except Exception as exc:
        if _is_missing_object_error(exc):
            return []
        raise


def guardar_tarifa(
    idtarifa: int,
    codigo: str,
    tarifa: str,
    valor: str | float,
    partida_cod: str,
    partida_id: str,
    tasa_id: int | str,
    formula: str,
    detalle: str,
    hora_dia: int,
    eslora_tneto: int,
    iva: int,
    ticket: int,
    activo: int,
    cambio_factura: int,
) -> int:
    """
    Guarda o actualiza una tarifa en la base de datos usando el procedimiento adecuado.
    """
    if settings.DEMO_MODE:
        # Retorna 20 (éxito de actualización) si es edición, o 1 si es inserción
        return 20 if idtarifa > 0 else 1

    try:
        try:
            valor_dec = float(valor)
        except (ValueError, TypeError):
            valor_dec = 0.0

        with closing(get_connection()) as connection:
            with closing(connection.cursor()) as cursor:
                if idtarifa > 0:
                    cursor.execute(
                        """
                        DECLARE @res INT;
                        EXEC dbo.SPJ_Update_Tarifas 
                            @sidtarifa = ?,
                            @sctarifa = ?, 
                            @starifa = ?, 
                            @svalor = ?, 
                            @scpartida = ?, 
                            @sidpartida = ?, 
                            @sidtasa = ?, 
                            @sformula = ?, 
                            @sdetalle = ?, 
                            @sidante = ?,
                            @shora_dia = ?, 
                            @seslora_tneto = ?, 
                            @siva = ?, 
                            @stikect = ?, 
                            @sidsenae = ?,
                            @sactivo = ?, 
                            @scambioFactura = ?, 
                            @sresul = @res OUTPUT;
                        SELECT @res AS resul;
                        """,
                        idtarifa,
                        codigo,
                        tarifa,
                        valor_dec,
                        partida_cod,
                        partida_id,
                        int(tasa_id),
                        formula,
                        detalle,
                        None,  # @sidante
                        int(hora_dia),
                        int(eslora_tneto),
                        int(iva),
                        int(ticket),
                        None,  # @sidsenae
                        int(activo),
                        int(cambio_factura),
                    )
                else:
                    cursor.execute(
                        """
                        DECLARE @res INT;
                        EXEC dbo.SPJ_insert_Tarifas 
                            @sctarifa = ?, 
                            @starifa = ?, 
                            @svalor = ?, 
                            @scpartida = ?, 
                            @sidpartida = ?, 
                            @sidtasa = ?, 
                            @sformula = ?, 
                            @sdetalle = ?, 
                            @shora_dia = ?, 
                            @seslora_tneto = ?, 
                            @siva = ?, 
                            @stikect = ?, 
                            @sactivo = ?, 
                            @scambioFactura = ?, 
                            @sresul = @res OUTPUT;
                        SELECT @res AS resul;
                        """,
                        codigo,
                        tarifa,
                        valor_dec,
                        partida_cod,
                        partida_id,
                        int(tasa_id),
                        formula,
                        detalle,
                        int(hora_dia),
                        int(eslora_tneto),
                        int(iva),
                        int(ticket),
                        int(activo),
                        int(cambio_factura),
                    )
                row = cursor.fetchone()
                if row:
                    return row[0]
                return 0
    except Exception:
        raise


def anular_tarifa(idtarifa: int | str) -> bool:
    """
    Anula una tarifa en la base de datos estableciendo idestado = 7 y activo = 0.
    """
    if settings.DEMO_MODE:
        return True

    try:
        with closing(get_connection()) as connection:
            with closing(connection.cursor()) as cursor:
                cursor.execute(
                    "UPDATE dbo.dim_tarifa SET idestado = 7, activo = 0 WHERE idtarifa = ?",
                    int(idtarifa)
                )
                return True
    except Exception:
        raise