from django.contrib import admin
from django.urls import path

from bitacora import views

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", views.login_view, name="login"),
    path("bitacora/", views.bitacora_home, name="bitacora_home"),
    path("tarifa/", views.tarifa_view, name="tarifa"),
    path("tarifa/listado/", views.tarifa_listado_view, name="tarifa_listado"),
    path("api/buscar-partida/", views.api_buscar_partida, name="api_buscar_partida"), # <--- RUTA NUEVA
    path("api/buscar-tasa/", views.api_buscar_tasa, name="api_buscar_tasa"),
    path("api/siguiente-codigo-tarifa/", views.api_siguiente_codigo, name="api_siguiente_codigo"),
    path("salir/", views.logout_view, name="logout"),
]