from __future__ import annotations

from datetime import date

from django.conf import settings
from django.shortcuts import redirect, render
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_http_methods

from .services.servicios_tpyc import obtener_servicios_tpyc


@never_cache
@require_http_methods(["GET"])
def servicios_tpyc_view(request):
    """
    Vista principal para el apartado de Servicios TPyC.
    """
    if not request.session.get("usuario_id"):
        return redirect("login")

    servicios = obtener_servicios_tpyc()

    return render(
        request,
        "bitacora/servicios_tpyc.html",
        {
            "demo_mode": getattr(settings, "DEMO_MODE", False),
            "usuario_nombre": request.session.get("usuario_nombre", ""),
            "usuario_login": request.session.get("usuario_login", ""),
            "usuario_cargo": request.session.get("usuario_cargo", ""),
            "fecha_actual": date.today(),
            "servicios": servicios,
        },
    )
