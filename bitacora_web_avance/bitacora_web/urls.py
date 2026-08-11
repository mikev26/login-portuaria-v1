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
    path("salir/", views.logout_view, name="logout"),
]
