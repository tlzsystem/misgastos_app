from django.urls import path
from .views import (
    CategoryCreateView,
    CategoryListView,
    CategoryToggleActiveView,
    CategoryUpdateView,
    DashboardView,
    MovementCreateView,
    MovementDeleteView,
    MovementListView,
    MovementUpdateView,
    SeedDefaultCategoriesView,
)

app_name = "finances"

urlpatterns = [
    # Dashboard mensual
    path("", DashboardView.as_view(), name="dashboard"),
    # Movimientos (Ingresos y Gastos)
    path("movimientos/", MovementListView.as_view(), name="movement_list"),
    path("movimientos/nuevo/", MovementCreateView.as_view(), name="movement_create"),
    path("movimientos/<int:pk>/editar/", MovementUpdateView.as_view(), name="movement_update"),
    path("movimientos/<int:pk>/eliminar/", MovementDeleteView.as_view(), name="movement_delete"),
    # Categorías por usuario
    path("categorias/", CategoryListView.as_view(), name="category_list"),
    path("categorias/nueva/", CategoryCreateView.as_view(), name="category_create"),
    path("categorias/<int:pk>/editar/", CategoryUpdateView.as_view(), name="category_update"),
    path(
        "categorias/<int:pk>/alternar-estado/",
        CategoryToggleActiveView.as_view(),
        name="category_toggle_active",
    ),
    path(
        "categorias/cargar-sugeridas/",
        SeedDefaultCategoriesView.as_view(),
        name="category_seed_defaults",
    ),
]
