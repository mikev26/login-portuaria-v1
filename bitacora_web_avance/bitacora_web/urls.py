from django.contrib import admin
from django.urls import path

from bitacora import views

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", views.login_view, name="login"),
    path("bitacora/", views.bitacora_home, name="bitacora_home"),
    path("tarifario/", views.tarifa_view, name="tarifa"),
    path("reporte/inec/", views.reporte_inec_view, name="reporte_inec"),
    path("registro-combustible/", views.registro_combustible_home, name="registro_combustible"),
    path(
        "registro-combustible/exportar-excel/",
        views.exportar_excel,
        name="registro_combustible_exportar",
    ),
    path(
        "registro-combustible/exportar-excel/validar/",
        views.exportar_excel_validar,
        name="registro_combustible_exportar_validar",
    ),
    path("tarifa/", views.tarifa_view, name="tarifa"),
    path("tarifa/inflacion/", views.tarifa_inflacion_view, name="tarifa_inflacion"),
    path("tarifa/listado/", views.tarifa_listado_view, name="tarifa_listado"),
    path("tarifa/guardar/", views.guardar_tarifa_view, name="tarifa_guardar"),
    path("tarifa/anular/", views.anular_tarifa_view, name="tarifa_anular"),
    path("tarifa/exportar/", views.exportar_tarifas_view, name="tarifa_exportar"),
    path("api/buscar-partida/", views.api_buscar_partida, name="api_buscar_partida"), # <--- RUTA NUEVA
    path("api/buscar-tasa/", views.api_buscar_tasa, name="api_buscar_tasa"),
    path("api/siguiente-codigo-tarifa/", views.api_siguiente_codigo, name="api_siguiente_codigo"),
    path("salir/", views.logout_view, name="logout"),
]