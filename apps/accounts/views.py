from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LoginView, LogoutView
from django.urls import reverse_lazy
from django.views.generic import CreateView, UpdateView

from apps.finances.services import seed_default_categories_for_user
from .forms import CustomAuthenticationForm, CustomUserCreationForm, UserProfileForm


class UserLoginView(LoginView):
    template_name = "accounts/login.html"
    authentication_form = CustomAuthenticationForm
    redirect_authenticated_user = True

    def form_valid(self, form):
        response = super().form_valid(form)
        user_display = self.request.user.first_name or self.request.user.username
        messages.success(self.request, f"¡Bienvenido de vuelta, {user_display}!")
        return response


class UserLogoutView(LogoutView):
    next_page = reverse_lazy("accounts:login")

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            messages.info(request, "Has cerrado sesión correctamente.")
        return super().dispatch(request, *args, **kwargs)


class UserRegisterView(CreateView):
    template_name = "accounts/register.html"
    form_class = CustomUserCreationForm
    success_url = reverse_lazy("finances:dashboard")

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            from django.shortcuts import redirect

            return redirect("finances:dashboard")
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        response = super().form_valid(form)
        if form.cleaned_data.get("create_default_categories"):
            seed_default_categories_for_user(self.object)
        login(self.request, self.object)
        messages.success(
            self.request,
            "¡Tu cuenta ha sido creada exitosamente! Ya puedes gestionar tus ingresos y gastos.",
        )
        return response


class UserProfileView(LoginRequiredMixin, UpdateView):
    template_name = "accounts/profile.html"
    form_class = UserProfileForm
    success_url = reverse_lazy("accounts:profile")

    def get_object(self, queryset=None):
        return self.request.user

    def form_valid(self, form):
        messages.success(self.request, "Tus datos de perfil han sido actualizados.")
        return super().form_valid(form)
