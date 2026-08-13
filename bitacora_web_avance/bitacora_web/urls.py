from django.contrib import admin
from django.urls import path

from bitacora import views

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", views.login_view, name="login"),
    path("bitacora/", views.bitacora_home, name="bitacora_home"),
<<<<<<< HEAD
    path("tarifa/", views.tarifa_view, name="tarifa"),
    path("tarifa/listado/", views.tarifa_listado_view, name="tarifa_listado"),
    path("tarifa/guardar/", views.guardar_tarifa_view, name="tarifa_guardar"),
    path("tarifa/anular/", views.anular_tarifa_view, name="tarifa_anular"),
    path("tarifa/exportar/", views.exportar_tarifas_view, name="tarifa_exportar"),
    path("api/buscar-partida/", views.api_buscar_partida, name="api_buscar_partida"), # <--- RUTA NUEVA
    path("api/buscar-tasa/", views.api_buscar_tasa, name="api_buscar_tasa"),
    path("api/siguiente-codigo-tarifa/", views.api_siguiente_codigo, name="api_siguiente_codigo"),
=======
    path("reporte/inec/", views.reporte_inec_view, name="reporte_inec"),
>>>>>>> origin/reporte
    path("salir/", views.logout_view, name="logout"),
]