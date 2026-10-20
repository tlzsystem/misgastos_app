"""URL configuration for MisGastos project."""
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("cuentas/", include("apps.accounts.urls", namespace="accounts")),
    path("", include("apps.finances.urls", namespace="finances")),
]
