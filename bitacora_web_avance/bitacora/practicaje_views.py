from __future__ import annotations

from datetime import date

from django.conf import settings
from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from django.shortcuts import redirect, render
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_http_methods

from .services.db_connection import DatabaseConfigurationError, DatabaseContractError
from .services.practicaje import obtener_datos_practicaje
from .services.practicaje_excel import crear_excel_practicaje


@never_cache
@require_http_methods(["GET"])
def datos_practicaje_home(request):
    if not request.session.get("usuario_id"):
        return redirect("login")

    fecha_inicio_valor = request.GET.get("fecha_inicio", "").strip()
    fecha_fin_valor = request.GET.get("fecha_fin", "").strip()
    fecha_inicio = None
    fecha_fin = None
    registros: list[dict[str, object]] = []
    consulta_realizada = False

    if fecha_inicio_valor or fecha_fin_valor:
        request.session.pop("reporte_practicaje_last", None)
        try:
            if not fecha_inicio_valor or not fecha_fin_valor:
                raise ValueError("Seleccione ambas fechas.")
            fecha_inicio = date.fromisoformat(fecha_inicio_valor)
            fecha_fin = date.fromisoformat(fecha_fin_valor)
            if fecha_inicio > fecha_fin:
                raise ValueError("La fecha inicial no puede ser posterior a la fecha final.")

            registros = obtener_datos_practicaje(fecha_inicio, fecha_fin)
            consulta_realizada = True
            request.session["reporte_practicaje_last"] = {
                "fecha_inicio": fecha_inicio.isoformat(),
                "fecha_fin": fecha_fin.isoformat(),
                "registros": _serializar_registros(registros),
            }
        except ValueError as exc:
            messages.error(
                request,
                str(exc) or "Ingrese un rango de fechas válido.",
            )
        except (DatabaseConfigurationError, DatabaseContractError):
            messages.error(request, "No fue posible obtener los datos de practicaje.")

    return render(
        request,
        "bitacora/datos_practicaje.html",
        {
            "demo_mode": settings.DEMO_MODE,
            "usuario_nombre": request.session.get("usuario_nombre", ""),
            "usuario_cargo": request.session.get("usuario_cargo", ""),
            "fecha_inicio": fecha_inicio_valor,
            "fecha_fin": fecha_fin_valor,
            "registros": registros,
            "consulta_realizada": consulta_realizada,
            "export_enabled": consulta_realizada and bool(registros),
            "fecha_emision": date.today(),
        },
    )


def _serializar_registros(registros: list[dict[str, object]]) -> list[dict[str, str]]:
    return [
        {
            clave: "" if valor is None else str(valor)
            for clave, valor in registro.items()
        }
        for registro in registros
    ]


@never_cache
@require_http_methods(["GET"])
def exportar_datos_practicaje_excel(request):
    if not request.session.get("usuario_id"):
        return redirect("login")

    ultima_busqueda = request.session.get("reporte_practicaje_last")
    if not ultima_busqueda or not ultima_busqueda.get("registros"):
        messages.info(request, "No existen registros de practicaje para exportar.")
        return redirect("datos_practicaje")

    fecha_inicio = ultima_busqueda.get("fecha_inicio", "")
    fecha_fin = ultima_busqueda.get("fecha_fin", "")
    try:
        contenido = crear_excel_practicaje(
            ultima_busqueda["registros"],
            fecha_inicio=fecha_inicio,
            fecha_fin=fecha_fin,
        )
    except ImportError:
        messages.error(request, "La dependencia 'openpyxl' no está instalada.")
        return redirect("datos_practicaje")

    rango_filename = (
        f"{fecha_inicio or 'sin_fecha'}_a_{fecha_fin or 'sin_fecha'}"
    )
    response = HttpResponse(
        contenido,
        content_type=(
            "application/vnd.openxmlformats-officedocument."
            "spreadsheetml.sheet"
        ),
    )
    response["Content-Disposition"] = (
        f'attachment; filename="DatosPracticaje_{rango_filename}.xlsx"'
    )
    return response


@never_cache
@require_http_methods(["GET"])
def validar_exportacion_practicaje(request):
    if not request.session.get("usuario_id"):
        return JsonResponse({"ok": False, "message": "Debe iniciar sesión."})

    ultima_busqueda = request.session.get("reporte_practicaje_last")
    if not ultima_busqueda:
        return JsonResponse({
            "ok": False,
            "message": "Primero debe realizar una búsqueda.",
        })
    if not ultima_busqueda.get("registros"):
        return JsonResponse({
            "ok": False,
            "message": "No existen registros para exportar.",
        })
    return JsonResponse({"ok": True})
