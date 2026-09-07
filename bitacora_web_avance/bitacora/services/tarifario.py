
from __future__ import annotations

import json
from contextlib import closing
from typing import Any

from django.conf import settings

from .db_connection import (
    DatabaseConfigurationError,
    _IDENTIFIER_RE,
    _PARAMETER_RE,
    _rows_as_dicts,
    execute_procedure,
    get_connection,
    bool_value,
    first_value,
    is_missing_object_error,
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
        if is_missing_object_error(exc):
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
        if is_missing_object_error(exc):
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
                    SET NOCOUNT ON;
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


def obtener_tarifas_existentes(estado: int = 1) -> list[dict[str, Any]]:
    """
    Ejecuta el procedimiento almacenado sp_v_tarifas para obtener el listado de tarifas.
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
                "permitir_cambio_valor": False,
                "aplica_inflacion": 1
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
                "permitir_cambio_valor": False,
                "aplica_inflacion": 0
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
                "permitir_cambio_valor": True,
                "aplica_inflacion": 1
            }
        ]
        
        # Filtro simulado en modo demostración
        if estado == 1:
            normalized = [t for t in normalized if t.get("activa") is True]
        elif estado == 0:
            normalized = [t for t in normalized if t.get("activa") is False]
        elif estado == 101:
            normalized = [
                {
                    "id": "1",
                    "codigo": "306",
                    "activa": True,
                    "tasa": "TASA CABOTAJE",
                    "tasa_id": "5",
                    "tarifa": "Prueba de tarifa exitosa",
                    "valor": "111110.0000",
                    "aplica_inflacion": 1
                },
                {
                    "id": "2",
                    "codigo": "307",
                    "activa": True,
                    "tasa": "TASA CABOTAJE",
                    "tasa_id": "5",
                    "tarifa": "Tarifa prueba 3 editado 3.1",
                    "valor": "5777.2000",
                    "aplica_inflacion": 1
                }
            ]
        # Si estado == 100 se devuelven todas las tarifas

        for t in normalized:
            t["json_data"] = json.dumps(t)
        return normalized

    try:
        tasa_map = {}
        try:
            tasas_db = obtener_tasa_por_id()
            for t_item in tasas_db:
                tasa_map[str(t_item["idtasa"])] = t_item["tasa"]
        except Exception:
            tasa_map = {
                "5": "TASA CABOTAJE",
                "7": "TASAS ESPECIFICAS",
                "2": "TASAS A LAS NAVES",
            }
        with closing(get_connection()) as connection:
            with closing(connection.cursor()) as cursor:
                cursor.execute("EXEC dbo.SPJ_v_tarifas ?", estado)
                rows = _rows_as_dicts(cursor)
                
                normalized = []
                for r in rows:
                    def str_or_empty(val: Any, default: str = "") -> str:
                        if val is None or str(val).strip().lower() == "none":
                            return default
                        return str(val).strip()

                    tasa_id_str = str_or_empty(first_value(r, ["tasa_id", "idtasa", "id_tasa"]))
                    
                    tasa_db_val = first_value(r, ["tasa", "tasa_nombre"])
                    if tasa_db_val and not str(tasa_db_val).isdigit():
                        tasa_nombre = str(tasa_db_val).strip()
                    else:
                        tasa_nombre = tasa_map.get(tasa_id_str, "")
                    
                    inflacion_val = first_value(r, ["inflacion", "aplicainflacion", "aplica_inflacion"])
                    if isinstance(inflacion_val, str):
                        aplica_inflacion = 1 if "aplica" in inflacion_val.lower() and "no aplica" not in inflacion_val.lower() else 0
                        aplica_inflacion_txt = inflacion_val
                    else:
                        aplica_inflacion = 1 if bool_value(inflacion_val) else 0
                        aplica_inflacion_txt = "Aplica inflación anual" if aplica_inflacion == 1 else "No aplica Inflación anual"

                    t_val = {
                        "id": str_or_empty(first_value(r, ["idtarifa", "id", "id_tarifa"])),
                        "codigo": str_or_empty(first_value(r, ["sctarifa", "codigo", "cod_tarifa", "cod"])),
                        "activa": bool_value(first_value(r, ["activa", "activo", "estado"], True)),
                        "tasa_id": tasa_id_str,
                        "tasa": tasa_nombre,
                        "tarifa": str_or_empty(first_value(r, ["tarifa", "nombre", "descripcion", "tarifa_desc"])),
                        "partida_cod": str_or_empty(first_value(r, ["partida_cod", "scpartida", "partida"])),
                        "partida_desc": str_or_empty(first_value(r, ["partida", "partida_desc", "nombrefinanza", "partidafinanzas"])),
                        "partida_cedula": str_or_empty(first_value(r, ["cedulafinanza", "partida_cedula", "cedula"])),
                        "partida_id": str_or_empty(first_value(r, ["idpartida", "partida_id"], "")),
                        "formula": str_or_empty(first_value(r, ["formula", "formula_calc"])),
                        "detalle": str_or_empty(first_value(r, ["detalle", "especificacion", "obs", "observacion"])),
                        "valor": str_or_empty(first_value(r, ["valor", "monto", "precio"], "0.0000")),
                        "s_ante": str_or_empty(first_value(r, ["s_ante", "s_antecedente", "id_ante"])),
                        "se_cobra_iva": bool_value(first_value(r, ["se_cobra_iva", "iva", "cobra_iva", "cobrar_iva"], False)),
                        "senae_cod": str_or_empty(first_value(r, ["senae_cod", "codigo_senae", "senae"])),
                        "senae_desc": str_or_empty(first_value(r, ["senae_desc", "detalle_senae"])),
                        "calc_param": "eslora" if first_value(r, ["eslora_toneto"]) == 1 else ("t_neto" if first_value(r, ["eslora_toneto"]) == 2 else "otros"),
                        "calc_unidad": "dia" if first_value(r, ["dia_hora"]) == 1 else ("horas" if first_value(r, ["dia_hora"]) == 2 else "cantidad"),
                        "ticket_srv": "vehiculo" if first_value(r, ["tikect"]) == 1 else ("muelle" if first_value(r, ["tikect"]) == 2 else "ninguno"),
                        "permitir_cambio_valor": bool_value(first_value(r, ["cambiofacturacion", "cambio_facturacion", "permitir_cambio_valor"], False)),
                        "aplica_inflacion": aplica_inflacion,
                        "aplica_inflacion_txt": aplica_inflacion_txt,
                    }
                    t_val["json_data"] = json.dumps(t_val)
                    normalized.append(t_val)
                return normalized
    except Exception as exc:
        if is_missing_object_error(exc):
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
    aplica_inflacion: int,
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
                        SET NOCOUNT ON;
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
                            @shora_dia = ?, 
                            @seslora_tneto = ?, 
                            @siva = ?, 
                            @stikect = ?, 
                            @sactivo = ?, 
                            @scambioFactura = ?, 
                            @sresul = @res OUTPUT,
                            @sinflacion = ?;
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
                        int(hora_dia),
                        int(eslora_tneto),
                        int(iva),
                        int(ticket),
                        int(activo),
                        int(cambio_factura),
                        int(aplica_inflacion),
                    )
                else:
                    cursor.execute(
                        """
                        SET NOCOUNT ON;
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
                            @sresul = @res OUTPUT,
                            @sinflacion = ?;
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
                        int(aplica_inflacion),
                    )
                row = cursor.fetchone()
                connection.commit()
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
                connection.commit()
                return True
    except Exception:
        raise


def guardar_inflacion(porcentaje: float, anio: int, idusuario: int, detalle: str = "", fecha_inflacion: str | None = None) -> int:
    """
    Aplica el ajuste por inflación a todas las tarifas configuradas (inflacion = 1).
    """
    if settings.DEMO_MODE:
        return 1

    try:
        with closing(get_connection()) as connection:
            with closing(connection.cursor()) as cursor:
                cursor.execute(
                    """
                    SET NOCOUNT ON;
                    DECLARE @res INT;
                    EXEC dbo.SPJ_Update_Inflacion
                        @pinflacion = ?,
                        @pano = ?,
                        @pidusuario = ?,
                        @pdetalle = ?,
                        @pfechaInflacion = ?,
                        @sresul = @res OUTPUT;
                    SELECT @res AS resul;
                    """,
                    porcentaje,
                    int(anio),
                    int(idusuario),
                    detalle,
                    fecha_inflacion,
                )
                row = cursor.fetchone()
                connection.commit()
                if row:
                    return row[0]
                return 1
    except Exception:
        raise


def obtener_cabeceras_historico_inflacion() -> list[dict[str, Any]]:
    """
    Retorna la lista de cabeceras de ajustes por inflación históricos
    disponibles en dbo.dim_TarifaCab.
    """
    if settings.DEMO_MODE:
        return [
            {
                "id_tarifaCab": 1,
                "anio_actual": 2026,
                "anio_anterior": 2025,
                "porcentaje_inflacion": 2.5000,
                "porcentajeAnterior": 0.0000,
                "detalle": "Ajuste anual por índice de inflación general 2026",
                "fechaInflacion": "2026-01-15",
                "fechaRegistro": "2026-01-15 10:30:00",
                "idUsuario": 1,
            }
        ]

    try:
        with closing(get_connection()) as connection:
            with closing(connection.cursor()) as cursor:
                cursor.execute("EXEC dbo.SPJ_HistoricoTarifas @listarCabeceras = 1")
                return _rows_as_dicts(cursor)
    except Exception as exc:
        if is_missing_object_error(exc):
            return []
        raise


def obtener_listado_cabeceras_historico() -> list[dict[str, Any]]:
    """
    Ejecuta dbo.SPJ_HistoricoTarifas @listarCabeceras = 1
    para obtener el historial de cabeceras registradas (Año, fechaRegistro, porcentaje, detalle).
    """
    if settings.DEMO_MODE:
        return [
            {
                "id_tarifaCab": 1,
                "idCabotaje": 1,
                "id": 1,
                "ano": 2026,
                "anio_actual": 2026,
                "anio_anterior": 2025,
                "porcentaje_inflacion": 2.50,
                "porcentaje_actual": 2.50,
                "detalle": "Ajuste tarifario anual 2026 demo",
                "fecha_inflacion": "2026-01-15",
                "fecha_registro": "2026-01-15 10:30",
                "id_usuario": 1,
            }
        ]

    try:
        with closing(get_connection()) as connection:
            with closing(connection.cursor()) as cursor:
                cursor.execute("EXEC dbo.SPJ_HistoricoTarifas @listarCabeceras = 1")
                rows = _rows_as_dicts(cursor)
                result = []
                for r in rows:
                    def str_or_empty(val: Any, default: str = "") -> str:
                        if val is None or str(val).strip().lower() == "none":
                            return default
                        return str(val).strip()

                    fecha_reg = first_value(r, ["fecharegistro", "fecha_registro"])
                    if hasattr(fecha_reg, "strftime"):
                        fecha_reg_str = fecha_reg.strftime("%Y-%m-%d %H:%M")
                    else:
                        fecha_reg_str = str_or_empty(fecha_reg)

                    fecha_inf = first_value(r, ["fechainflacion", "fecha_inflacion"])
                    if hasattr(fecha_inf, "strftime"):
                        fecha_inf_str = fecha_inf.strftime("%Y-%m-%d")
                    else:
                        fecha_inf_str = str_or_empty(fecha_inf)

                    item = {
                        "id_tarifaCab": first_value(r, ["id_tarifacab", "idcabotaje", "id"]),
                        "idCabotaje": first_value(r, ["id_tarifacab", "idcabotaje", "id"]),
                        "id": first_value(r, ["id_tarifacab", "idcabotaje", "id"]),
                        "ano": first_value(r, ["ano", "anio_actual", "anio"]),
                        "anio_actual": first_value(r, ["ano", "anio_actual", "anio"]),
                        "anio_anterior": first_value(r, ["anio_anterior", "ano_anterior"]),
                        "porcentaje_inflacion": float(first_value(r, ["porcentaje_inflacion", "porcentajeactual", "porcentaje_actual"]) or 0),
                        "porcentaje_actual": float(first_value(r, ["porcentaje_inflacion", "porcentajeactual", "porcentaje_actual"]) or 0),
                        "detalle": str_or_empty(first_value(r, ["detalle", "justificacion"])),
                        "fecha_inflacion": fecha_inf_str,
                        "fecha_registro": fecha_reg_str,
                        "id_usuario": first_value(r, ["idusuario", "id_usuario"]),
                    }
                    result.append(item)
                return result
    except Exception:
        logger.exception("Error al consultar listado de cabeceras históricas")
        return []


def obtener_historico_tarifas(id_cabotaje: int | None = None, ano: int | None = None) -> list[dict[str, Any]]:
    """
    Ejecuta dbo.SPJ_HistoricoTarifas pasando idCabotaje o ano
    para obtener el listado histórico de tarifas con sus valores congelados
    y los cálculos de inflación aplicados en ese evento.
    """
    if settings.DEMO_MODE:
        target_ano = int(ano) if ano else 2026
        target_id = int(id_cabotaje) if id_cabotaje else 1
        return [
            {
                "nro": 1,
                "tasa": "TASA CABOTAJE",
                "codigo": "01",
                "tarifa": "USO DE MUELLES - MARGINALES",
                "valor": "0.1600",
                "valor_anterior": "0.1600",
                "inflacion": 1,
                "aplica_inflacion": 1,
                "aplica_inflacion_txt": "Aplica inflación anual",
                "porcentaje_inflacion": 2.5000,
                "tarifa_inflacion": "0.0040",
                "valor_final": "0.1640",
                "idtarifa": 1,
                "idtasa": 5,
                "activo": 1,
                "id_tarifaCab": target_id,
                "ano": target_ano,
                "ano_anterior": target_ano - 1,
                "fecha_inflacion": "2026-01-15",
                "detalle": "Ajuste histórico demo",
            },
            {
                "nro": 2,
                "tasa": "TASA CABOTAJE",
                "codigo": "28",
                "tarifa": "MUELLES MARGINALES.-MANTE.ABARLOAMIENTO",
                "valor": "0.1400",
                "valor_anterior": "0.1400",
                "inflacion": 1,
                "aplica_inflacion": 1,
                "aplica_inflacion_txt": "Aplica inflación anual",
                "porcentaje_inflacion": 2.5000,
                "tarifa_inflacion": "0.0035",
                "valor_final": "0.1435",
                "idtarifa": 2,
                "idtasa": 5,
                "activo": 1,
                "id_tarifaCab": target_id,
                "ano": target_ano,
                "ano_anterior": target_ano - 1,
                "fecha_inflacion": "2026-01-15",
                "detalle": "Ajuste histórico demo",
            }
        ]

    try:
        with closing(get_connection()) as connection:
            with closing(connection.cursor()) as cursor:
                id_val = int(id_cabotaje) if id_cabotaje else None
                ano_val = int(ano) if ano else None
                try:
                    cursor.execute(
                        "EXEC dbo.SPJ_HistoricoTarifas @id = ?, @ano = ?",
                        id_val,
                        ano_val,
                    )
                    rows = _rows_as_dicts(cursor)
                except Exception:
                    # Fallback si el procedimiento en la BD del usuario aún no incluye el parámetro @ano
                    rows = []
                    if not id_val and ano_val:
                        cursor.execute(
                            "SELECT id FROM dbo.dim_TarifaCab WHERE ano = ? ORDER BY id DESC",
                            ano_val,
                        )
                        cab_ids = [row[0] for row in cursor.fetchall() if row and row[0]]
                        for c_id in cab_ids:
                            cursor.execute("EXEC dbo.SPJ_HistoricoTarifas @id = ?", c_id)
                            rows.extend(_rows_as_dicts(cursor))
                cab_user_map = {}
                if any(first_value(r, ["idusuario", "id_usuario"]) is None for r in rows):
                    try:
                        cursor.execute("SELECT id, idUsuario FROM dbo.dim_TarifaCab")
                        for u_row in cursor.fetchall():
                            if u_row and u_row[0] is not None and u_row[1] is not None:
                                cab_user_map[u_row[0]] = u_row[1]
                    except Exception:
                        pass

                normalized = []
                for r in rows:
                    def str_or_empty(val: Any, default: str = "") -> str:
                        if val is None or str(val).strip().lower() == "none":
                            return default
                        return str(val).strip()

                    inflacion_val = first_value(r, ["inflacion", "aplicainflacion", "aplica_inflacion"])
                    if isinstance(inflacion_val, str):
                        aplica_inflacion = 1 if "aplica" in inflacion_val.lower() and "no aplica" not in inflacion_val.lower() else 0
                    else:
                        aplica_inflacion = 1 if bool_value(inflacion_val) else 0

                    cab_id_val = first_value(r, ["id_tarifacab", "idcabotaje", "id"])
                    id_usr = first_value(r, ["idusuario", "id_usuario"])
                    if id_usr is None and cab_id_val in cab_user_map:
                        id_usr = cab_user_map[cab_id_val]

                    item = {
                        "nro": first_value(r, ["nro", "item", "row_number"]),
                        "tasa": str_or_empty(first_value(r, ["tasa", "tasa_nombre"])),
                        "codigo": str_or_empty(first_value(r, ["sctarifa", "codigo", "cod_tarifa"])),
                        "tarifa": str_or_empty(first_value(r, ["tarifa", "nombre", "descripcion"])),
                        "valor": str_or_empty(first_value(r, ["valor", "valor_anterior", "monto"]), "0.0000"),
                        "valor_anterior": str_or_empty(first_value(r, ["valor_anterior", "valor"]), "0.0000"),
                        "inflacion": aplica_inflacion,
                        "aplica_inflacion": aplica_inflacion,
                        "aplica_inflacion_txt": "Aplica inflación anual" if aplica_inflacion == 1 else "No aplica Inflación anual",
                        "porcentaje_inflacion": float(first_value(r, ["porcentajeactual", "porcentaje_actual", "porcentajeinflacion"]) or 0),
                        "porcentaje_actual": float(first_value(r, ["porcentajeactual", "porcentaje_actual"]) or 0),
                        "tarifa_inflacion": str_or_empty(first_value(r, ["tarifainflacion", "tarifa_inflacion"]), "0.0000"),
                        "valor_final": str_or_empty(first_value(r, ["valorfinaltarifa", "valor_final"]), "0.0000"),
                        "idtarifa": first_value(r, ["idtarifa", "id_tarifa"]),
                        "idtasa": first_value(r, ["idtasa", "id_tasa"]),
                        "activo": bool_value(first_value(r, ["activo", "activa"], True)),
                        "id_tarifaCab": cab_id_val,
                        "ano": first_value(r, ["ano", "anio", "anio_actual"]),
                        "ano_anterior": first_value(r, ["ano_anterior", "anio_anterior"]),
                        "fecha_inflacion": str_or_empty(first_value(r, ["fechainflacion", "fecha_inflacion"])),
                        "fecha_registro": str_or_empty(first_value(r, ["fecharegistro", "fecha_registro"])),
                        "detalle": str_or_empty(first_value(r, ["detalle", "justificacion"])),
                        "id_usuario": id_usr,
                    }
                    normalized.append(item)
                return normalized
    except Exception as exc:
        if is_missing_object_error(exc):
            return []
        raise