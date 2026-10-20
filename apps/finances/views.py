from decimal import Decimal
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Count, DecimalField, Q, Sum, Value
from django.db.models.functions import Coalesce
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.utils import timezone
from django.views import View
from django.views.generic import CreateView, DeleteView, ListView, TemplateView, UpdateView

from .forms import CategoryForm, MovementFilterForm, MovementForm
from .models import Category, Movement
from .services import MONTH_NAMES_ES, get_monthly_summary, seed_default_categories_for_user


class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = "finances/dashboard.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        today = timezone.localdate()

        try:
            year = int(self.request.GET.get("year", today.year))
            if year < 2000 or year > 2100:
                year = today.year
        except (ValueError, TypeError):
            year = today.year

        try:
            month = int(self.request.GET.get("month", today.month))
            if month < 1 or month > 12:
                month = today.month
        except (ValueError, TypeError):
            month = today.month

        summary = get_monthly_summary(self.request.user, year, month)
        context.update(summary)

        # Month and year selector lists
        context["month_choices"] = [(m, name) for m, name in MONTH_NAMES_ES.items()]
        context["year_choices"] = list(range(today.year + 1, today.year - 5, -1))
        context["has_active_categories"] = (
            Category.objects.for_user(self.request.user).active().exists()
        )
        context["active_categories_count"] = (
            Category.objects.for_user(self.request.user).active().count()
        )
        return context


class MovementListView(LoginRequiredMixin, ListView):
    model = Movement
    template_name = "finances/movement_list.html"
    context_object_name = "movements"
    paginate_by = 15

    def get_queryset(self):
        qs = (
            Movement.objects.for_user(self.request.user)
            .select_related("category")
            .order_by("-date", "-created_at", "-id")
        )

        self.filter_form = MovementFilterForm(self.request.GET or None, user=self.request.user)
        if self.filter_form.is_valid():
            data = self.filter_form.cleaned_data
            if data.get("year"):
                qs = qs.filter(date__year=int(data["year"]))
            if data.get("month"):
                qs = qs.filter(date__month=int(data["month"]))
            if data.get("movement_type"):
                qs = qs.filter(category__category_type=data["movement_type"])
            if data.get("category"):
                qs = qs.filter(category=data["category"])
            if data.get("q"):
                query = data["q"].strip()
                qs = qs.filter(
                    Q(description__icontains=query)
                    | Q(notes__icontains=query)
                    | Q(category__name__icontains=query)
                )

        self.filtered_qs = qs
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        totals = self.filtered_qs.aggregate(
            filtered_income=Coalesce(
                Sum("amount", filter=Q(category__category_type=Category.CategoryType.INCOME)),
                Decimal("0.00"),
            ),
            filtered_expense=Coalesce(
                Sum("amount", filter=Q(category__category_type=Category.CategoryType.EXPENSE)),
                Decimal("0.00"),
            ),
            total_count=Count("id"),
        )
        context["filter_form"] = self.filter_form
        context["filtered_income"] = totals["filtered_income"]
        context["filtered_expense"] = totals["filtered_expense"]
        context["filtered_balance"] = totals["filtered_income"] - totals["filtered_expense"]
        context["filtered_count"] = totals["total_count"]
        return context


class MovementCreateView(LoginRequiredMixin, CreateView):
    model = Movement
    form_class = MovementForm
    template_name = "finances/movement_form.html"
    success_url = reverse_lazy("finances:movement_list")

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Registrar Nuevo Movimiento"
        context["is_edit"] = False
        initial_type = self.request.GET.get("type", Category.CategoryType.EXPENSE)
        if initial_type not in (Category.CategoryType.EXPENSE, Category.CategoryType.INCOME):
            initial_type = Category.CategoryType.EXPENSE
        context["initial_type"] = initial_type
        context["categories_meta"] = getattr(context["form"], "categories_meta", [])
        context["has_active_categories"] = (
            Category.objects.for_user(self.request.user).active().exists()
        )
        return context

    def form_valid(self, form):
        form.instance.user = self.request.user
        response = super().form_valid(form)
        tipo = "Ingreso" if self.object.is_income else "Gasto"
        messages.success(
            self.request,
            f"{tipo} «{self.object.description}» registrado correctamente.",
        )
        next_url = self.request.POST.get("next") or self.request.GET.get("next")
        if next_url and next_url.startswith("/"):
            return redirect(next_url)
        return response


class MovementUpdateView(LoginRequiredMixin, UpdateView):
    model = Movement
    form_class = MovementForm
    template_name = "finances/movement_form.html"
    success_url = reverse_lazy("finances:movement_list")

    def get_queryset(self):
        # Strictly isolate movements to the authenticated user
        return Movement.objects.for_user(self.request.user).select_related("category")

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Editar Movimiento"
        context["is_edit"] = True
        context["initial_type"] = self.object.category.category_type
        context["categories_meta"] = getattr(context["form"], "categories_meta", [])
        context["has_active_categories"] = True
        return context

    def form_valid(self, form):
        form.instance.user = self.request.user
        response = super().form_valid(form)
        messages.success(
            self.request,
            f"El movimiento «{self.object.description}» ha sido actualizado.",
        )
        return response


class MovementDeleteView(LoginRequiredMixin, DeleteView):
    model = Movement
    template_name = "finances/movement_confirm_delete.html"
    success_url = reverse_lazy("finances:movement_list")
    context_object_name = "movement"

    def get_queryset(self):
        return Movement.objects.for_user(self.request.user).select_related("category")

    def form_valid(self, form):
        desc = self.object.description
        response = super().form_valid(form)
        messages.success(self.request, f"El movimiento «{desc}» fue eliminado permanentemente.")
        return response


class CategoryListView(LoginRequiredMixin, ListView):
    model = Category
    template_name = "finances/category_list.html"
    context_object_name = "categories"

    def get_queryset(self):
        today = timezone.localdate()
        return (
            Category.objects.for_user(self.request.user)
            .annotate(
                movements_count=Count("movements", distinct=True),
                current_month_total=Coalesce(
                    Sum(
                        "movements__amount",
                        filter=Q(
                            movements__date__year=today.year,
                            movements__date__month=today.month,
                        ),
                    ),
                    Value(Decimal("0.00"), output_field=DecimalField()),
                ),
            )
            .order_by("-is_active", "category_type", "name")
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        all_cats = list(context["categories"])
        context["expense_categories"] = [
            c for c in all_cats if c.category_type == Category.CategoryType.EXPENSE
        ]
        context["income_categories"] = [
            c for c in all_cats if c.category_type == Category.CategoryType.INCOME
        ]
        context["active_count"] = sum(1 for c in all_cats if c.is_active)
        context["inactive_count"] = sum(1 for c in all_cats if not c.is_active)
        today = timezone.localdate()
        context["current_month_name"] = MONTH_NAMES_ES.get(today.month, "")
        return context


class CategoryCreateView(LoginRequiredMixin, CreateView):
    model = Category
    form_class = CategoryForm
    template_name = "finances/category_form.html"
    success_url = reverse_lazy("finances:category_list")

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def get_initial(self):
        initial = super().get_initial()
        cat_type = self.request.GET.get("type")
        if cat_type in (Category.CategoryType.EXPENSE, Category.CategoryType.INCOME):
            initial["category_type"] = cat_type
        return initial

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Nueva Categoría"
        context["is_edit"] = False
        return context

    def form_valid(self, form):
        form.instance.user = self.request.user
        response = super().form_valid(form)
        messages.success(
            self.request,
            f"La categoría «{self.object.name}» ({self.object.get_category_type_display()}) fue creada exitosamente.",
        )
        return response


class CategoryUpdateView(LoginRequiredMixin, UpdateView):
    model = Category
    form_class = CategoryForm
    template_name = "finances/category_form.html"
    success_url = reverse_lazy("finances:category_list")

    def get_queryset(self):
        return Category.objects.for_user(self.request.user)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = f"Editar Categoría: {self.object.name}"
        context["is_edit"] = True
        return context

    def form_valid(self, form):
        form.instance.user = self.request.user
        response = super().form_valid(form)
        messages.success(
            self.request,
            f"La categoría «{self.object.name}» fue actualizada correctamente.",
        )
        return response


class CategoryToggleActiveView(LoginRequiredMixin, View):
    """Toggle active/inactive status of a user's category (POST only)."""

    def post(self, request, pk):
        category = get_object_or_404(Category.objects.for_user(request.user), pk=pk)
        category.is_active = not category.is_active
        category.save(update_fields=["is_active", "updated_at"])

        if category.is_active:
            messages.success(
                request,
                f"La categoría «{category.name}» ha sido reactivada y ya está disponible para nuevos movimientos.",
            )
        else:
            messages.warning(
                request,
                f"La categoría «{category.name}» fue desactivada. Se conservarán todos sus movimientos históricos.",
            )
        return redirect("finances:category_list")


class SeedDefaultCategoriesView(LoginRequiredMixin, View):
    """Allow an existing user to load the default starter categories."""

    def post(self, request):
        created = seed_default_categories_for_user(request.user)
        if created > 0:
            messages.success(
                request,
                f"Se agregaron {created} categorías sugeridas a tu cuenta.",
            )
        else:
            messages.info(
                request,
                "Ya cuentas con todas las categorías sugeridas en tu listado.",
            )
        return redirect("finances:category_list")
