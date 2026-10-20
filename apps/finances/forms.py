from django import forms
from django.db.models import Q
from django.utils import timezone

from .models import Category, Movement
from .services import MONTH_NAMES_ES

INPUT_CLASSES = (
    "w-full rounded-xl border border-slate-200 bg-white px-4 py-2.5 text-sm "
    "text-slate-800 placeholder-slate-400 shadow-xs transition focus:border-indigo-500 "
    "focus:outline-none focus:ring-3 focus:ring-indigo-500/15"
)

SELECT_CLASSES = (
    "w-full rounded-xl border border-slate-200 bg-white px-3.5 py-2.5 text-sm "
    "text-slate-800 shadow-xs transition focus:border-indigo-500 "
    "focus:outline-none focus:ring-3 focus:ring-indigo-500/15"
)


class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = [
            "name",
            "category_type",
            "color",
            "icon",
            "monthly_budget",
            "description",
            "is_active",
        ]
        widgets = {
            "name": forms.TextInput(
                attrs={
                    "class": INPUT_CLASSES,
                    "placeholder": "Ej. Supermercado, Sueldo, Gimnasio...",
                }
            ),
            "category_type": forms.Select(attrs={"class": SELECT_CLASSES}),
            "color": forms.Select(attrs={"class": SELECT_CLASSES}),
            "icon": forms.Select(attrs={"class": SELECT_CLASSES}),
            "monthly_budget": forms.NumberInput(
                attrs={
                    "class": INPUT_CLASSES,
                    "placeholder": "Opcional (Ej. 250000)",
                    "step": "0.01",
                    "min": "0",
                }
            ),
            "description": forms.TextInput(
                attrs={
                    "class": INPUT_CLASSES,
                    "placeholder": "Breve descripción opcional de esta categoría",
                }
            ),
            "is_active": forms.CheckboxInput(
                attrs={
                    "class": "h-4 w-4 rounded border-slate-300 text-indigo-600 focus:ring-indigo-500",
                }
            ),
        }

    def __init__(self, *args, user=None, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)

    def clean(self):
        cleaned_data = super().clean()
        name = cleaned_data.get("name")
        category_type = cleaned_data.get("category_type")

        if self.user and name and category_type:
            qs = Category.objects.filter(
                user=self.user,
                name__iexact=name.strip(),
                category_type=category_type,
            )
            if self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise forms.ValidationError(
                    "Ya tienes una categoría con este nombre y tipo. Elige otro nombre o edita la existente."
                )
        if name:
            cleaned_data["name"] = name.strip()
        return cleaned_data


class MovementForm(forms.ModelForm):
    class Meta:
        model = Movement
        fields = [
            "category",
            "amount",
            "description",
            "date",
            "payment_method",
            "notes",
        ]
        widgets = {
            "category": forms.Select(
                attrs={
                    "class": SELECT_CLASSES,
                    "id": "id_category",
                }
            ),
            "amount": forms.NumberInput(
                attrs={
                    "class": INPUT_CLASSES + " font-semibold text-base",
                    "placeholder": "0.00",
                    "step": "0.01",
                    "min": "0.01",
                }
            ),
            "description": forms.TextInput(
                attrs={
                    "class": INPUT_CLASSES,
                    "placeholder": "Ej. Compra mensual supermercado, Pago de luz, Sueldo...",
                }
            ),
            "date": forms.DateInput(
                format="%Y-%m-%d",
                attrs={
                    "type": "date",
                    "class": INPUT_CLASSES,
                },
            ),
            "payment_method": forms.Select(attrs={"class": SELECT_CLASSES}),
            "notes": forms.Textarea(
                attrs={
                    "class": INPUT_CLASSES,
                    "rows": 3,
                    "placeholder": "Detalles adicionales, número de boleta o comentarios (opcional)...",
                }
            ),
        }

    def __init__(self, *args, user=None, initial_type=None, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)
        if not self.instance.pk and not self.initial.get("date"):
            self.initial["date"] = timezone.localdate().strftime("%Y-%m-%d")

        if user:
            # Show active categories belonging to this user, plus the currently assigned category if editing
            filter_q = Q(user=user, is_active=True)
            if self.instance.pk and self.instance.category_id:
                filter_q |= Q(pk=self.instance.category_id, user=user)

            categories_qs = Category.objects.filter(filter_q).order_by("category_type", "name")
            self.fields["category"].queryset = categories_qs
            self.fields["category"].empty_label = "Selecciona una categoría..."

            # Build metadata list for dynamic client-side filtering by Ingreso / Gasto
            self.categories_meta = [
                {
                    "id": cat.id,
                    "name": f"{cat.name}{' (Inactiva)' if not cat.is_active else ''}",
                    "type": cat.category_type,
                    "type_display": cat.get_category_type_display(),
                    "color": cat.color,
                    "icon": cat.icon,
                    "is_active": cat.is_active,
                }
                for cat in categories_qs
            ]
        else:
            self.fields["category"].queryset = Category.objects.none()
            self.categories_meta = []

    def clean_category(self):
        category = self.cleaned_data.get("category")
        if category and self.user and category.user_id != self.user.id:
            raise forms.ValidationError("La categoría seleccionada no pertenece a tu usuario.")
        return category

    def clean(self):
        cleaned_data = super().clean()
        if self.user:
            self.instance.user = self.user
        return cleaned_data


class MovementFilterForm(forms.Form):
    TYPE_CHOICES = [
        ("", "Todos los tipos"),
        (Category.CategoryType.EXPENSE, "Solo Gastos"),
        (Category.CategoryType.INCOME, "Solo Ingresos"),
    ]

    month = forms.ChoiceField(
        label="Mes",
        required=False,
        widget=forms.Select(attrs={"class": SELECT_CLASSES}),
    )
    year = forms.ChoiceField(
        label="Año",
        required=False,
        widget=forms.Select(attrs={"class": SELECT_CLASSES}),
    )
    movement_type = forms.ChoiceField(
        label="Tipo",
        choices=TYPE_CHOICES,
        required=False,
        widget=forms.Select(attrs={"class": SELECT_CLASSES}),
    )
    category = forms.ModelChoiceField(
        label="Categoría",
        queryset=Category.objects.none(),
        required=False,
        empty_label="Todas las categorías",
        widget=forms.Select(attrs={"class": SELECT_CLASSES}),
    )
    q = forms.CharField(
        label="Buscar",
        required=False,
        widget=forms.TextInput(
            attrs={
                "class": INPUT_CLASSES,
                "placeholder": "Buscar por concepto o nota...",
            }
        ),
    )

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        today = timezone.localdate()
        month_choices = [("", "Todos los meses")] + [
            (str(m), f"{m:02d} - {name}") for m, name in MONTH_NAMES_ES.items()
        ]
        year_choices = [("", "Todos los años")] + [
            (str(y), str(y)) for y in range(today.year + 1, today.year - 6, -1)
        ]
        self.fields["month"].choices = month_choices
        self.fields["year"].choices = year_choices

        if user:
            self.fields["category"].queryset = Category.objects.for_user(user).order_by(
                "category_type", "name"
            )
