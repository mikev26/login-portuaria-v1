from __future__ import annotations

import json
import json
from datetime import date

from django.conf import settings
from django.core.serializers.json import DjangoJSONEncoder
from django.shortcuts import redirect, render
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_http_methods

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

from .services.servicios_tpyc import (
    obtener_servicios_tpyc,
    obtener_tarifas_activas_tpyc,
    obtener_grupos_servicio,
    obtener_medidas_servicio,
    insertar_servicio_tpyc,
    actualizar_servicio_tpyc,
)


@never_cache
@require_http_methods(["GET"])
def servicios_tpyc_view(request):
    """
    Vista principal para el apartado de Servicios TPyC.
    """
    if not request.session.get("usuario_id"):
        return redirect("login")

    servicios = obtener_servicios_tpyc()
    tarifas = obtener_tarifas_activas_tpyc()
    grupos = obtener_grupos_servicio()
    medidas = obtener_medidas_servicio()

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
            "servicios_json": json.dumps(servicios, cls=DjangoJSONEncoder),
            "tarifas_json": json.dumps(tarifas, cls=DjangoJSONEncoder),
            "grupos": grupos,
            "grupos_json": json.dumps(grupos, cls=DjangoJSONEncoder),
            "medidas": medidas,
            "medidas_json": json.dumps(medidas, cls=DjangoJSONEncoder),
        },
    )


@csrf_exempt
@require_http_methods(["POST"])
def guardar_servicio_tpyc_view(request):
    """
    Guarda o actualiza un servicio ejecutando dbo.SPJ_Insert_Servicios
    o dbo.SPJ_Update_Servicios según corresponda.
    """
    if not request.session.get("usuario_id"):
        return JsonResponse({"success": False, "mensaje": "Sesión no válida o expirada."}, status=401)

    try:
        data = json.loads(request.body.decode("utf-8")) if request.body else {}
    except Exception:
        data = request.POST.dict()

    idservicio_raw = data.get("idservicio") or data.get("id")
    idservicio = int(idservicio_raw) if idservicio_raw and str(idservicio_raw).isdigit() else None

    servicio = data.get("servicio", "").strip()
    medida = data.get("medida", "").strip()
    grupo = data.get("grupo", "").strip()
    detalle = data.get("detalle", "").strip()

    t_n = 1 if data.get("t_n") in (True, 1, "1", "true") else 0
    t_e = 1 if data.get("t_e") in (True, 1, "1", "true") else 0
    t_i = 1 if data.get("t_i") in (True, 1, "1", "true") else 0

    cidtarifa = data.get("cidtarifa") or 0
    eidtarifa = data.get("eidtarifa") or 0
    nidtarifa = data.get("nidtarifa") or 0

    cdeta = data.get("cdeta", "")
    edeta = data.get("edeta", "")

    idgrupo = data.get("idgrupo")
    idmedida = data.get("idmedida")

    try:
        idgrupo_int = int(idgrupo) if idgrupo is not None and str(idgrupo).isdigit() else None
    except Exception:
        idgrupo_int = None

    try:
        idmedida_int = int(idmedida) if idmedida is not None and str(idmedida).isdigit() else None
    except Exception:
        idmedida_int = None

    if idservicio and idservicio > 0:
        resultado = actualizar_servicio_tpyc(
            idservicio=idservicio,
            servicio=servicio,
            medida=medida,
            grupo=grupo,
            detalle=detalle,
            t_n=t_n,
            t_e=t_e,
            t_i=t_i,
            cidtarifa=cidtarifa,
            eidtarifa=eidtarifa,
            nidtarifa=nidtarifa,
        )
    else:
        resultado = insertar_servicio_tpyc(
            servicio=servicio,
            medida=medida,
            grupo=grupo,
            detalle=detalle,
            t_n=t_n,
            t_e=t_e,
            t_i=t_i,
            cidtarifa=cidtarifa,
            eidtarifa=eidtarifa,
            nidtarifa=nidtarifa,
            cdeta=cdeta,
            edeta=edeta,
            civa=0,
            idgrupo=idgrupo_int,
            idmedida=idmedida_int,
        )

    status_code = 200 if resultado.get("success") else 400
    return JsonResponse(resultado, status=status_code)


