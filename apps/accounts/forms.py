from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm

from .recaptcha import get_client_ip, is_recaptcha_enabled, verify_recaptcha_token

User = get_user_model()

INPUT_CLASSES = (
    "w-full rounded-xl border border-slate-200 bg-white px-4 py-2.5 text-sm "
    "text-slate-800 placeholder-slate-400 shadow-xs transition focus:border-indigo-500 "
    "focus:outline-none focus:ring-3 focus:ring-indigo-500/15"
)


class ReCaptchaValidationMixin:
    """Mixin to validate Google reCAPTCHA v2 token on form submission."""

    recaptcha_error_messages = {
        "required": "Por favor, marca la casilla «No soy un robot» para continuar.",
        "invalid": "La verificación de Google reCAPTCHA falló o expiró. Inténtalo nuevamente.",
    }

    def validate_recaptcha(self):
        if not is_recaptcha_enabled():
            return
        token = self.data.get("g-recaptcha-response", "").strip()
        if not token:
            raise forms.ValidationError(
                self.recaptcha_error_messages["required"],
                code="recaptcha_required",
            )
        remote_ip = get_client_ip(getattr(self, "request", None))
        if not verify_recaptcha_token(token, remote_ip=remote_ip):
            raise forms.ValidationError(
                self.recaptcha_error_messages["invalid"],
                code="recaptcha_invalid",
            )


class CustomAuthenticationForm(ReCaptchaValidationMixin, AuthenticationForm):
    username = forms.CharField(
        label="Nombre de usuario",
        widget=forms.TextInput(
            attrs={
                "class": INPUT_CLASSES,
                "placeholder": "Ej. juanperez",
                "autofocus": True,
                "autocomplete": "username",
            }
        ),
    )
    password = forms.CharField(
        label="Contraseña",
        strip=False,
        widget=forms.PasswordInput(
            attrs={
                "class": INPUT_CLASSES,
                "placeholder": "••••••••",
                "autocomplete": "current-password",
            }
        ),
    )

    def clean(self):
        self.validate_recaptcha()
        return super().clean()


class CustomUserCreationForm(ReCaptchaValidationMixin, UserCreationForm):
    first_name = forms.CharField(
        label="Nombre",
        max_length=150,
        required=True,
        widget=forms.TextInput(
            attrs={
                "class": INPUT_CLASSES,
                "placeholder": "Tu nombre",
            }
        ),
    )
    last_name = forms.CharField(
        label="Apellido",
        max_length=150,
        required=False,
        widget=forms.TextInput(
            attrs={
                "class": INPUT_CLASSES,
                "placeholder": "Tu apellido (opcional)",
            }
        ),
    )
    email = forms.EmailField(
        label="Correo electrónico",
        required=True,
        widget=forms.EmailInput(
            attrs={
                "class": INPUT_CLASSES,
                "placeholder": "nombre@ejemplo.com",
            }
        ),
    )
    create_default_categories = forms.BooleanField(
        label="Crear categorías iniciales sugeridas (Sueldo, Alimentación, Vivienda, Transporte, etc.)",
        required=False,
        initial=True,
        widget=forms.CheckboxInput(
            attrs={
                "class": "h-4 w-4 rounded border-slate-300 text-indigo-600 focus:ring-indigo-500",
            }
        ),
    )

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("username", "first_name", "last_name", "email")
        widgets = {
            "username": forms.TextInput(
                attrs={
                    "class": INPUT_CLASSES,
                    "placeholder": "Elige un nombre de usuario",
                }
            ),
        }

    def __init__(self, *args, request=None, **kwargs):
        self.request = request
        super().__init__(*args, **kwargs)
        self.fields["password1"].widget.attrs.update(
            {"class": INPUT_CLASSES, "placeholder": "Mínimo 8 caracteres"}
        )
        self.fields["password2"].widget.attrs.update(
            {"class": INPUT_CLASSES, "placeholder": "Repite tu contraseña"}
        )

    def clean_email(self):
        email = self.cleaned_data.get("email", "").strip().lower()
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("Ya existe una cuenta registrada con este correo electrónico.")
        return email

    def clean(self):
        cleaned_data = super().clean()
        self.validate_recaptcha()
        return cleaned_data


class UserProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ("first_name", "last_name", "email")
        labels = {
            "first_name": "Nombre",
            "last_name": "Apellido",
            "email": "Correo electrónico",
        }
        widgets = {
            "first_name": forms.TextInput(attrs={"class": INPUT_CLASSES}),
            "last_name": forms.TextInput(attrs={"class": INPUT_CLASSES}),
            "email": forms.EmailInput(attrs={"class": INPUT_CLASSES}),
        }
