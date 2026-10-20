from django.urls import path
from .views import UserLoginView, UserLogoutView, UserProfileView, UserRegisterView

app_name = "accounts"

urlpatterns = [
    path("ingresar/", UserLoginView.as_view(), name="login"),
    path("salir/", UserLogoutView.as_view(), name="logout"),
    path("registro/", UserRegisterView.as_view(), name="register"),
    path("perfil/", UserProfileView.as_view(), name="profile"),
]
