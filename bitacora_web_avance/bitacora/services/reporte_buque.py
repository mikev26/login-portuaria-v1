from .db_connection import (
    DatabaseConfigurationError,
    DatabaseContractError,
    get_connection,
)


def obtener_datos_reporte_buques(
    f_desde,
    f_hasta,
    chk_buque=False,
    sel_buque=None,
    chk_tiponave=False,
    sel_tiponave=None,
    chk_armador=False,
    sel_armador=None,
    chk_procedencia=False,
    sel_procedencia=None,
    chk_destino=False,
    sel_destino=None,
    chk_estado=False,
    sel_estado=None,
    en_puerto_filtro=False,
):

    registros = _ejecutar_reporte(
        f_desde,
        f_hasta,
    )

    registros = _normalizar_registros(registros)

    def normalizar_filtro(valor):
        if valor is None:
            return []

        if isinstance(valor, (list, tuple)):
            return [
                str(v).strip()
                for v in valor
                if str(v).strip()
            ]

        valor = str(valor).strip()

        if not valor:
            return []

        return [valor]

    valores_buque = normalizar_filtro(sel_buque)
    valores_tiponave = normalizar_filtro(sel_tiponave)
    valores_armador = normalizar_filtro(sel_armador)
    valores_procedencia = normalizar_filtro(sel_procedencia)
    valores_destino = normalizar_filtro(sel_destino)
    valores_estado = normalizar_filtro(sel_estado)

    if en_puerto_filtro:
        registros = [
            registro
            for registro in registros
            if not _tiene_fecha_zarpe(
                registro.get("fecha_zarpe")
            )
        ]

    if chk_buque and valores_buque:
        registros = [
            registro
            for registro in registros
            if str(
                registro.get("buque", "")
            ).strip() in valores_buque
        ]

    if chk_tiponave and valores_tiponave:
        registros = [
            registro
            for registro in registros
            if str(
                registro.get("tipo_de_trafico", "")
            ).strip() in valores_tiponave
        ]

    if chk_armador and valores_armador:
        registros = [
            registro
            for registro in registros
            if str(
                registro.get("armador", "")
            ).strip() in valores_armador
        ]

    if chk_procedencia and valores_procedencia:
        registros = [
            registro
            for registro in registros
            if str(
                registro.get("procedencia", "")
            ).strip() in valores_procedencia
        ]

    if chk_destino and valores_destino:
        registros = [
            registro
            for registro in registros
            if str(
                registro.get("destino", "")
            ).strip() in valores_destino
        ]

    if chk_estado and valores_estado:
        registros = [
            registro
            for registro in registros
            if str(
                registro.get("estado", "")
            ).strip() in valores_estado
        ]

    return registros

def obtener_catalogos_reporte_buques(
    f_desde,
    f_hasta,
):
    """
    Obtiene los catálogos usando las mismas fechas
    seleccionadas por el usuario.

    IMPORTANTE:
    Ya no utiliza fechas fijas.
    """

    registros = _ejecutar_reporte(
        f_desde,
        f_hasta,
    )

    registros = _normalizar_registros(registros)

    return {
        "buques": _valores_unicos(
            registros,
            "buque",
        ),

        "tipos_nave": _valores_unicos(
            registros,
            "tipo_de_trafico",
        ),

        "armadores": _valores_unicos(
            registros,
            "armador",
        ),

        "procedencias": _valores_unicos(
            registros,
            "procedencia",
        ),

        "destinos": _valores_unicos(
            registros,
            "destino",
        ),

        "estados": _valores_unicos(
            registros,
            "estado",
        ),

        "banderas": _valores_unicos(
            registros,
            "bandera",
        ),

        "scregistros": _valores_unicos(
            registros,
            "scregistro",
        ),
    }


def _ejecutar_reporte(
    f_desde,
    f_hasta,
):
    """
    Ejecuta:

        SPJ_ReporteRegistroBuques ?, ?
    """

    if not f_desde or not f_hasta:
        raise DatabaseContractError(
            "Debe indicar la fecha desde y hasta."
        )

    try:

        with get_connection() as conn:

            cursor = conn.cursor()

            cursor.execute(
                "EXEC SPJ_ReporteRegistroBuques ?, ?",
                f_desde,
                f_hasta,
            )

            if cursor.description is None:
                return []

            columns = [
                column[0]
                for column in cursor.description
            ]

            rows = cursor.fetchall()

            return [
                dict(zip(columns, row))
                for row in rows
            ]

    except (
        DatabaseConfigurationError,
        DatabaseContractError,
    ):
        raise

    except Exception as exc:

        raise DatabaseContractError(
            f"Error ejecutando el reporte de buques: {exc}"
        ) from exc


def _normalizar_registros(registros):
    """
    Normaliza los nombres de las columnas de fecha
    para que el template siempre trabaje con:

        fecha_arribo
        fecha_zarpe
    """

    for registro in registros:

        if (
            "fecha_arrivo" in registro
            and "fecha_arribo" not in registro
        ):
            registro["fecha_arribo"] = (
                registro["fecha_arrivo"]
            )

        elif (
            "f_arribo" in registro
            and "fecha_arribo" not in registro
        ):
            registro["fecha_arribo"] = (
                registro["f_arribo"]
            )

        if (
            "f_zarpe" in registro
            and "fecha_zarpe" not in registro
        ):
            registro["fecha_zarpe"] = (
                registro["f_zarpe"]
            )

    return registros


def _tiene_fecha_zarpe(valor):
    """
    Determina si el registro tiene fecha de zarpe.
    """

    if valor is None:
        return False

    texto = str(valor).strip()

    return texto not in (
        "",
        "None",
        "NULL",
        "NoneType",
    )


def _valores_unicos(
    registros,
    campo,
):
    """
    Obtiene valores únicos, ordenados
    y sin valores vacíos.
    """

    return sorted(
        {
            str(registro.get(campo)).strip()
            for registro in registros
            if registro.get(campo) is not None
            and str(
                registro.get(campo)
            ).strip()
        }
    )