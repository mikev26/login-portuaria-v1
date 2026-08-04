from django.contrib import admin
from django.urls import path

from bitacora import views

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", views.login_view, name="login"),
    path("bitacora/", views.bitacora_home, name="bitacora_home"),
    path("tarifa/", views.tarifa_view, name="tarifa"),
    path("salir/", views.logout_view, name="logout"),
]
