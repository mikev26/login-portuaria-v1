from django.contrib import admin
from django.urls import path

from bitacora import views
from bitacora import practicaje_views

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", views.login_view, name="login"),
    path("bitacora/", views.bitacora_home, name="bitacora_home"),
    path("bitacora/exportar-excel/",views.exportar_bitacora_excel,name="bitacora_exportar_excel"),
    path("tarifario/", views.tarifa_view, name="tarifa"),
    path("reporte/inec/", views.reporte_inec_view, name="reporte_inec"),
    path("registro-combustible/", views.registro_combustible_home, name="registro_combustible"),
    path("datos-practicaje/", practicaje_views.datos_practicaje_home, name="datos_practicaje"),
    path("datos-practicaje/exportar-excel/", practicaje_views.exportar_datos_practicaje_excel, name="datos_practicaje_exportar"),
    path("datos-practicaje/exportar-excel/validar/", practicaje_views.validar_exportacion_practicaje, name="datos_practicaje_exportar_validar"),
    path("datos-abiertos/", views.datos_abiertos_home, name="datos_abiertos"),
    path("datos-abiertos/exportar-excel/", views.datos_abiertos_exportar_view, name="datos_abiertos_exportar",),
    path("registro-combustible/exportar-excel/", views.exportar_excel, name="registro_combustible_exportar"),
    path("registro-combustible/exportar-excel/validar/", views.exportar_excel_validar, name="registro_combustible_exportar_validar"),
    path("tarifa/", views.tarifa_view, name="tarifa"),
    path("tarifa/listado/", views.tarifa_listado_view, name="tarifa_listado"),
    path("tarifa/guardar/", views.guardar_tarifa_view, name="tarifa_guardar"),
    path("tarifa/anular/", views.anular_tarifa_view, name="tarifa_anular"),
    path("tarifa/exportar/", views.exportar_tarifas_view, name="tarifa_exportar"),
    path("api/buscar-partida/", views.api_buscar_partida, name="api_buscar_partida"), 
    path("api/buscar-tasa/", views.api_buscar_tasa, name="api_buscar_tasa"),
    path("api/siguiente-codigo-tarifa/", views.api_siguiente_codigo, name="api_siguiente_codigo"),
    path( "reporte/buques/", views.reporte_buque_view, name="reporte_buque"),
    path( "reporte/buques/exportar/", views.exportar_reporte_buques, name="exportar_reporte_buques"),
    # -----------------------------------------
    path("modulo-buques/", views.index, name="modulo_buques_home"),
    path("api/buques", views.obtener_buques, name="obtener_buques"),
    path("api/registros", views.obtener_registros, name="obtener_registros"),
    path("api/operadores_movimiento", views.obtener_operadores_movimiento, name="obtener_operadores_movimiento"),
    path("api/operadores_listados", views.obtener_operadores_listados, name="obtener_operadores_listados"),
    path("api/exportar-buques", views.exportar_buques, name="exportar_buques"),
    path("salir/", views.logout_view, name="logout"),
    path("cambiar-contrasena/", views.cambiar_contrasena_view, name="cambiar_contrasena"),
]