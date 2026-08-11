from django.contrib import admin
from django.urls import path

from bitacora import views

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", views.login_view, name="login"),
    path("bitacora/", views.bitacora_home, name="bitacora_home"),
    path("tarifario/", views.tarifa_view, name="tarifa"),
    path("reporte/inec/", views.reporte_inec_view, name="reporte_inec"),
    path("salir/", views.logout_view, name="logout"),
]
