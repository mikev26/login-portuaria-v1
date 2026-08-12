import logging
from datetime import date
import io
import os

from django.conf import settings
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.shortcuts import redirect, render
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_http_methods

from .forms import LoginForm, RegistroCombustibleFilterForm
from .db import (
    DatabaseConfigurationError,
    DatabaseContractError,
    obtener_buques_artesanales,
    obtener_buques_industriales,
    obtener_reporte_combustible,
    obtener_turnos_usuario,
    validar_usuario,
)

logger = logging.getLogger(__name__)


def _iniciar_sesion(request, datos_usuario, turnos):
    request.session.cycle_key()
    request.session["usuario_id"] = datos_usuario["idusuario"]
    request.session["usuario_login"] = datos_usuario["usuario"]
    request.session["usuario_nombre"] = datos_usuario["nombre"]
    request.session["usuario_cargo"] = turnos[0].get("cargo") or datos_usuario.get(
        "cargo",
        "Inspector",
    )


@never_cache
@require_http_methods(["GET", "POST"])
def login_view(request):
    if request.session.get("usuario_id"):
        return redirect("bitacora_home")

    form = LoginForm(request.POST or None)

    if request.method == "POST":
        if form.is_valid():
            usuario = form.cleaned_data["usuario"]
            clave = form.cleaned_data["clave"]

            try:
                datos_usuario = validar_usuario(usuario, clave)

                if not datos_usuario:
                    messages.error(request, "Usuario o contraseña incorrectos.")
                else:
                    # La segunda condición de acceso es aparecer en el procedimiento
                    # de turnos activos: fecha_s NULL, activo <> 7 y bitacora = 1.
                    turnos = obtener_turnos_usuario(datos_usuario["idusuario"])
                    if not turnos:
                        messages.error(
                            request,
                            "El usuario es válido, pero no tiene un turno activo "
                            "habilitado para la bitácora.",
                        )
                    else:
                        _iniciar_sesion(request, datos_usuario, turnos)
                        return redirect("bitacora_home")

            except (DatabaseConfigurationError, DatabaseContractError) as exc:
                logger.exception("Configuración o contrato de base de datos inválido")
                messages.error(request, str(exc))
            except Exception:
                logger.exception("Error inesperado al validar el acceso")
                messages.error(
                    request,
                    "No fue posible comunicarse con la base de datos. "
                    "Revise la conexión o consulte al administrador.",
                )

    return render(
        request,
        "bitacora/login.html",
        {"demo_mode": settings.DEMO_MODE, "form": form},
    )


@never_cache
@require_http_methods(["GET"])
def bitacora_home(request):
    idusuario = request.session.get("usuario_id")
    if not idusuario:
        return redirect("login")

    try:
        turnos = obtener_turnos_usuario(idusuario)
        if not turnos:
            request.session.flush()
            messages.error(
                request,
                "Su turno ya no está activo o perdió el permiso de bitácora.",
            )
            return redirect("login")

        industriales = obtener_buques_industriales()
        artesanales = obtener_buques_artesanales()

    except (DatabaseConfigurationError, DatabaseContractError) as exc:
        logger.exception("Error de configuración al abrir la bitácora")
        messages.error(request, str(exc))
        turnos, industriales, artesanales = [], [], []
    except Exception:
        logger.exception("Error inesperado al cargar la bitácora")
        messages.error(
            request,
            "No fue posible cargar los datos de la bitácora desde SQL Server.",
        )
        turnos, industriales, artesanales = [], [], []

    return render(
        request,
        "bitacora/home.html",
        {
            "usuario_nombre": request.session.get("usuario_nombre"),
            "usuario_login": request.session.get("usuario_login"),
            "usuario_cargo": request.session.get("usuario_cargo"),
            "turnos": turnos,
            "buques_industriales": industriales,
            "buques_artesanales": artesanales,
            "demo_mode": settings.DEMO_MODE,
        },
    )


@never_cache
@require_http_methods(["GET"])
def registro_combustible_home(request):
    if not request.session.get("usuario_id"):
        return redirect("login")

    form = RegistroCombustibleFilterForm(request.GET or None)
    registros: list[dict[str, object]] = []

    fecha_emision = date.today()
    fecha_desde = None
    fecha_hasta = None

    ajax_response = {
        "fecha_emision": fecha_emision.isoformat(),
        "fecha_desde": "",
        "fecha_hasta": "",
        "rows": [],
        "messages": [],
    }

    if form.is_valid():
        fecha_desde = form.cleaned_data.get("fecha_inicio")
        fecha_hasta = form.cleaned_data.get("fecha_fin")
        if fecha_desde:
            ajax_response["fecha_desde"] = fecha_desde.isoformat()
        if fecha_hasta:
            ajax_response["fecha_hasta"] = fecha_hasta.isoformat()

    if request.GET.get("buscar") == "1":
        if form.is_valid():
            try:
                registros = obtener_reporte_combustible(
                    form.cleaned_data["fecha_inicio"],
                    form.cleaned_data["fecha_fin"],
                )
                for registro in registros:
                    if "fecha_ingresa" in registro:
                        registro["fecha_ingresa"] = registro.get("fecha_ingresa", "")
                        registro["fecha"] = registro["fecha_ingresa"]
                    if "tikect" in registro:
                        registro["c_tikect"] = registro.get("tikect", "")
                        registro["c_ticket"] = registro["c_tikect"]
                    elif "c_tikect" in registro:
                        registro["c_ticket"] = registro.get("c_tikect", "")
                # Guardar último resultado de búsqueda en sesión para la exportación.
                try:
                    def _serialize_value(v):
                        if v is None:
                            return ""
                        # fechas y datetimes a ISO
                        if hasattr(v, "isoformat"):
                            try:
                                return v.isoformat()
                            except Exception:
                                pass
                        return str(v)

                    session_rows = [
                        {k: _serialize_value(v) for k, v in (reg.items())}
                        for reg in registros
                    ]
                    request.session["reporte_combustible_last"] = {
                        "fecha_desde": fecha_desde.isoformat() if fecha_desde else "",
                        "fecha_hasta": fecha_hasta.isoformat() if fecha_hasta else "",
                        "registros": session_rows,
                    }
                except Exception:
                    # No bloquear la búsqueda si la sesión no puede serializarse.
                    logger.exception("No fue posible guardar el resultado en sesión para exportación")
                if not registros:
                    msg = "No existen registros para el rango de fechas seleccionado."
                    messages.info(request, msg)
                    ajax_response["messages"].append({"text": msg, "tags": "info"})
            except (DatabaseConfigurationError, DatabaseContractError) as exc:
                logger.exception("Error de base de datos al obtener el reporte")
                generic_msg = "No fue posible obtener los datos del reporte. Revise la conexión o consulte al administrador."
                messages.error(request, generic_msg)
                ajax_response["messages"].append({"text": generic_msg, "tags": "error"})
            except Exception:
                logger.exception("Error inesperado al obtener el reporte de combustible")
                generic_msg = "No fue posible cargar los datos desde SQL Server. Revise la conexión o consulte al administrador."
                messages.error(request, generic_msg)
                ajax_response["messages"].append({"text": generic_msg, "tags": "error"})
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    ajax_response["messages"].append({"text": str(error), "tags": "error"})
            messages.error(
                request,
                "Complete correctamente Fecha Desde y Fecha Hasta antes de buscar.",
            )

    is_ajax = request.headers.get("x-requested-with") == "XMLHttpRequest" or "application/json" in request.headers.get("accept", "")

    if is_ajax:
        ajax_response["rows"] = [
            {
                "fecha_ingresa": str(registro.get("fecha_ingresa", registro.get("fecha", ""))),
                "c_tikect": str(registro.get("c_tikect", registro.get("c_ticket", registro.get("tikect", "")))),
                "guia": str(registro.get("guia", "")),
                "idplaca": str(registro.get("idplaca", "")),
                "chofer": str(registro.get("chofer", "")),
                "codbuque": str(registro.get("codbuque", "")),
                "buque": str(registro.get("buque", "")),
                "matricula": str(registro.get("matricula", "")),
                "galones": str(registro.get("galones", "")),
                "motivo": str(registro.get("motivo", "")),
            }
            for registro in registros
        ]
        return JsonResponse(ajax_response)

    return render(
        request,
        "bitacora/registro_combustible.html",
        {
            "demo_mode": settings.DEMO_MODE,
            "form": form,
            "registros": registros,
            "usuario_nombre": request.session.get("usuario_nombre", ""),
            "fecha_emision": fecha_emision,
            "fecha_desde": fecha_desde,
            "fecha_hasta": fecha_hasta,
        },
    )


def _obtener_datos_exportacion(request):
    """Obtiene los registros y rango de fechas para exportación.
    
    Primero consulta la sesión. Si no existe pero la petición contiene
    los parámetros GET (fecha_inicio y fecha_fin), vuelve a ejecutar la búsqueda.
    """
    last = request.session.get("reporte_combustible_last")
    if last and last.get("registros"):
        return last

    form = RegistroCombustibleFilterForm(request.GET or None)
    if form.is_valid():
        try:
            fecha_inicio = form.cleaned_data["fecha_inicio"]
            fecha_fin = form.cleaned_data["fecha_fin"]
            registros = obtener_reporte_combustible(fecha_inicio, fecha_fin)
            for registro in registros:
                if "fecha_ingresa" in registro:
                    registro["fecha_ingresa"] = registro.get("fecha_ingresa", "")
                    registro["fecha"] = registro["fecha_ingresa"]
                if "tikect" in registro:
                    registro["c_tikect"] = registro.get("tikect", "")
                    registro["c_ticket"] = registro["c_tikect"]
                elif "c_tikect" in registro:
                    registro["c_ticket"] = registro.get("c_tikect", "")

            def _serialize_value(v):
                if v is None:
                    return ""
                if hasattr(v, "isoformat"):
                    try:
                        return v.isoformat()
                    except Exception:
                        pass
                return str(v)

            session_rows = [
                {k: _serialize_value(v) for k, v in reg.items()}
                for reg in registros
            ]
            datos = {
                "fecha_desde": fecha_inicio.isoformat(),
                "fecha_hasta": fecha_fin.isoformat(),
                "registros": session_rows,
            }
            request.session["reporte_combustible_last"] = datos
            return datos
        except Exception:
            logger.exception("Error al recuperar registros de exportación vía parámetros GET")
            pass

    return last


@require_http_methods(["GET"])
def exportar_excel(request):
    """Exporta a Excel el último resultado de búsqueda almacenado en sesión o parámetros GET."""
    if not request.session.get("usuario_id"):
        return redirect("login")

    last = _obtener_datos_exportacion(request)
    if not last:
        messages.error(request, "Primero debe realizar una búsqueda para exportar la información.")
        return redirect("registro_combustible")

    registros = last.get("registros", [])
    if not registros:
        messages.info(request, "No existen registros para exportar.")
        return redirect("registro_combustible")

    # Verificar plantilla
    template_path = (
        getattr(settings, "RUTA_PLANTILLA_EXCEL", "")
        or os.getenv("RUTA_PLANTILLA_EXCEL", "")
        or ""
    ).strip()
    if not template_path or not os.path.exists(template_path):
        messages.error(
            request,
            f"Plantilla de Excel no encontrada. Configure la ruta en RUTA_PLANTILLA_EXCEL.",
        )
        return redirect("registro_combustible")

    try:
        try:
            import openpyxl
        except Exception:
            messages.error(request, "La dependencia 'openpyxl' para generar Excel no está instalada.")
            return redirect("registro_combustible")

        with open(template_path, "rb") as f:
            template_bytes = io.BytesIO(f.read())

        wb = openpyxl.load_workbook(template_bytes)
        ws = wb["controlcombustible"] if "controlcombustible" in wb.sheetnames else wb.active

        def safe_write_cell(ws, r, c, val):
            cell = ws.cell(row=r, column=c)
            if cell.__class__.__name__ != "MergedCell":
                cell.value = val

        # Escribir fecha de emisión en Celda A4
        fecha_emision_str = date.today().strftime("%d/%m/%Y")
        safe_write_cell(ws, 4, 1, f"Fecha de Emisión : Manta, {fecha_emision_str}")

        # Formatear fechas desde y hasta para Celda A5
        def _fmt_fecha(val):
            if not val:
                return "—"
            if hasattr(val, "strftime"):
                return val.strftime("%d/%m/%Y")
            val_str = str(val).split("T")[0]
            parts = val_str.split("-")
            if len(parts) == 3 and len(parts[0]) == 4:
                return f"{parts[2]}/{parts[1]}/{parts[0]}"
            return str(val)

        f_desde_str = _fmt_fecha(last.get("fecha_desde"))
        f_hasta_str = _fmt_fecha(last.get("fecha_hasta"))

        safe_write_cell(
            ws,
            5,
            1,
            f"F.Desde: {f_desde_str}               F.Hasta :      {f_hasta_str}",
        )

        def first_value(row, keys):
            if isinstance(row, dict):
                for key in keys:
                    val = row.get(key)
                    if val is not None and str(val).strip() != "":
                        return val
            elif isinstance(row, (list, tuple)):
                for val in row:
                    if val is not None and str(val).strip() != "":
                        return val
            return ""

        start_row = 8
        for idx, reg in enumerate(registros, start=start_row):
            fila = [
                first_value(reg, ("fecha_ingresa", "fecha", "fecha_registro", "fecha_mov")),
                first_value(reg, ("c_tikect", "c_ticket", "tikect", "ticket", "tickets")),
                first_value(reg, ("guia", "guia_r", "guia_no")),
                first_value(reg, ("idplaca", "placa")),
                first_value(reg, ("chofer", "conductor")),
                first_value(reg, ("licencia", "licencia_conductor", "licencia_no")),
                first_value(reg, ("codbuque", "cod_buque", "scbuque")),
                first_value(reg, ("buque", "nombre")),
                first_value(reg, ("matricula", "n_matricula")),
                first_value(reg, ("galones", "cantidad_litros", "litros")),
                first_value(reg, ("motivo",)),
                first_value(reg, ("estado",)),
                first_value(reg, ("tipo_carro", "tipo carro", "tipo")),
            ]

            for col_idx, value in enumerate(fila, start=1):
                safe_write_cell(ws, idx, col_idx, value)

        output = io.BytesIO()
        wb.save(output)
        output.seek(0)

        # Sanitizar nombre de archivo a caracteres ASCII puros para evitar errores en Content-Disposition
        clean_desde = f_desde_str.replace("/", "-").replace("—", "sin_fecha").strip()
        clean_hasta = f_hasta_str.replace("/", "-").replace("—", "sin_fecha").strip()
        raw_filename = f"ReporteCombustible_{clean_desde}_{clean_hasta}.xlsx"
        filename_ascii = "".join(c if c.isalnum() or c in "._-" else "_" for c in raw_filename)

        response = HttpResponse(
            output.read(),
            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
        response["Content-Disposition"] = f'attachment; filename="{filename_ascii}"'
        return response

    except Exception as exc:
        logger.exception("Error al generar el archivo Excel")
        messages.error(
            request,
            f"Ocurrió un error al generar el archivo Excel: {exc}",
        )
        return redirect("registro_combustible")


@require_http_methods(["GET"])
def exportar_excel_validar(request):
    """Valida via AJAX si la exportación puede ejecutarse."""
    if not request.session.get("usuario_id"):
        return JsonResponse({"ok": False, "message": "Debe iniciar sesión para exportar.", "level": "error"})

    last = _obtener_datos_exportacion(request)
    if not last:
        return JsonResponse({
            "ok": False,
            "message": "Primero debe realizar una búsqueda para exportar la información.",
            "level": "info",
        })

    registros = last.get("registros", [])
    if not registros:
        return JsonResponse({"ok": False, "message": "No existen registros para exportar.", "level": "info"})

    template_path = (
        getattr(settings, "RUTA_PLANTILLA_EXCEL", "")
        or os.getenv("RUTA_PLANTILLA_EXCEL", "")
        or ""
    ).strip()
    if not template_path or not os.path.exists(template_path):
        return JsonResponse({
            "ok": False,
            "message": f"Plantilla de Excel no encontrada en '{template_path}'. Configure la ruta en RUTA_PLANTILLA_EXCEL.",
            "level": "error",
        })

    return JsonResponse({"ok": True})


@require_http_methods(["POST"])
def logout_view(request):
    request.session.flush()
    messages.success(request, "Sesión cerrada correctamente.")
    return redirect("login")
