import calendar
from datetime import date
from decimal import Decimal
from django.db.models import Count, Q, Sum
from django.db.models.functions import Coalesce

from .models import Category, Movement

MONTH_NAMES_ES = {
    1: "Enero",
    2: "Febrero",
    3: "Marzo",
    4: "Abril",
    5: "Mayo",
    6: "Junio",
    7: "Julio",
    8: "Agosto",
    9: "Septiembre",
    10: "Octubre",
    11: "Noviembre",
    12: "Diciembre",
}

DEFAULT_CATEGORIES = [
    # Ingresos
    {
        "name": "Sueldo / Salario",
        "category_type": Category.CategoryType.INCOME,
        "color": "#10b981",
        "icon": "briefcase",
        "description": "Remuneración mensual principal",
    },
    {
        "name": "Freelance / Honorarios",
        "category_type": Category.CategoryType.INCOME,
        "color": "#06b6d4",
        "icon": "laptop",
        "description": "Ingresos por servicios independientes y proyectos",
    },
    {
        "name": "Inversiones / Dividendos",
        "category_type": Category.CategoryType.INCOME,
        "color": "#8b5cf6",
        "icon": "trending-up",
        "description": "Intereses, depósitos a plazo o fondos",
    },
    {
        "name": "Otros Ingresos",
        "category_type": Category.CategoryType.INCOME,
        "color": "#14b8a6",
        "icon": "gift",
        "description": "Reembolsos, regalos o ingresos extraordinarios",
    },
    # Gastos
    {
        "name": "Vivienda y Arriendo",
        "category_type": Category.CategoryType.EXPENSE,
        "color": "#6366f1",
        "icon": "home",
        "description": "Arriendo, dividendo, gastos comunes y hogar",
    },
    {
        "name": "Supermercado y Alimentación",
        "category_type": Category.CategoryType.EXPENSE,
        "color": "#f97316",
        "icon": "shopping-cart",
        "description": "Compras de supermercado, feria y despensa",
    },
    {
        "name": "Restaurantes y Delivery",
        "category_type": Category.CategoryType.EXPENSE,
        "color": "#ec4899",
        "icon": "utensils",
        "description": "Salidas a comer, cafeterías y pedidos a domicilio",
    },
    {
        "name": "Transporte y Combustible",
        "category_type": Category.CategoryType.EXPENSE,
        "color": "#3b82f6",
        "icon": "car",
        "description": "Transporte público, bencina, peajes y apps de movilidad",
    },
    {
        "name": "Servicios y Cuentas",
        "category_type": Category.CategoryType.EXPENSE,
        "color": "#eab308",
        "icon": "zap",
        "description": "Luz, agua, gas, internet y telefonía",
    },
    {
        "name": "Salud y Farmacia",
        "category_type": Category.CategoryType.EXPENSE,
        "color": "#f43f5e",
        "icon": "heart-pulse",
        "description": "Consultas médicas, medicamentos y deporte",
    },
    {
        "name": "Entretenimiento y Suscripciones",
        "category_type": Category.CategoryType.EXPENSE,
        "color": "#8b5cf6",
        "icon": "film",
        "description": "Streaming, cine, conciertos y pasatiempos",
    },
]


def seed_default_categories_for_user(user) -> int:
    """Create starter income and expense categories for a user if they don't exist yet."""
    created_count = 0
    for item in DEFAULT_CATEGORIES:
        _, created = Category.objects.get_or_create(
            user=user,
            name=item["name"],
            category_type=item["category_type"],
            defaults={
                "color": item["color"],
                "icon": item["icon"],
                "description": item["description"],
                "is_active": True,
            },
        )
        if created:
            created_count += 1
    return created_count


def get_adjacent_months(year: int, month: int):
    """Return (prev_year, prev_month) and (next_year, next_month)."""
    if month == 1:
        prev_year, prev_month = year - 1, 12
    else:
        prev_year, prev_month = year, month - 1

    if month == 12:
        next_year, next_month = year + 1, 1
    else:
        next_year, next_month = year, month + 1

    return (prev_year, prev_month), (next_year, next_month)


def get_monthly_summary(user, year: int, month: int) -> dict:
    """Compute comprehensive financial metrics and chart datasets for a user's given month."""
    period_qs = Movement.objects.for_user(user).for_period(year, month).select_related("category")

    totals = period_qs.aggregate(
        total_income=Coalesce(
            Sum("amount", filter=Q(category__category_type=Category.CategoryType.INCOME)),
            Decimal("0.00"),
        ),
        total_expense=Coalesce(
            Sum("amount", filter=Q(category__category_type=Category.CategoryType.EXPENSE)),
            Decimal("0.00"),
        ),
        income_count=Count("id", filter=Q(category__category_type=Category.CategoryType.INCOME)),
        expense_count=Count("id", filter=Q(category__category_type=Category.CategoryType.EXPENSE)),
    )

    total_income = totals["total_income"]
    total_expense = totals["total_expense"]
    net_balance = total_income - total_expense

    if total_income > 0:
        savings_rate = round(((total_income - total_expense) / total_income) * Decimal("100"), 1)
        expense_ratio = min(round((total_expense / total_income) * Decimal("100"), 1), Decimal("100.0"))
    else:
        savings_rate = Decimal("0.0")
        expense_ratio = Decimal("100.0") if total_expense > 0 else Decimal("0.0")

    # Previous month comparison
    (prev_year, prev_month), (next_year, next_month) = get_adjacent_months(year, month)
    prev_totals = (
        Movement.objects.for_user(user)
        .for_period(prev_year, prev_month)
        .aggregate(
            prev_income=Coalesce(
                Sum("amount", filter=Q(category__category_type=Category.CategoryType.INCOME)),
                Decimal("0.00"),
            ),
            prev_expense=Coalesce(
                Sum("amount", filter=Q(category__category_type=Category.CategoryType.EXPENSE)),
                Decimal("0.00"),
            ),
        )
    )
    prev_expense = prev_totals["prev_expense"]
    if prev_expense > 0:
        expense_variation_pct = round(((total_expense - prev_expense) / prev_expense) * Decimal("100"), 1)
    else:
        expense_variation_pct = None

    # Breakdown by category
    category_rows = (
        period_qs.values(
            "category__id",
            "category__name",
            "category__category_type",
            "category__color",
            "category__icon",
            "category__monthly_budget",
            "category__is_active",
        )
        .annotate(
            total=Coalesce(Sum("amount"), Decimal("0.00")),
            count=Count("id"),
        )
        .order_by("-total")
    )

    expense_by_category = []
    income_by_category = []

    for row in category_rows:
        item = {
            "id": row["category__id"],
            "name": row["category__name"],
            "color": row["category__color"],
            "icon": row["category__icon"],
            "monthly_budget": row["category__monthly_budget"],
            "is_active": row["category__is_active"],
            "total": row["total"],
            "count": row["count"],
        }
        if row["category__category_type"] == Category.CategoryType.EXPENSE:
            pct = round((row["total"] / total_expense) * Decimal("100"), 1) if total_expense > 0 else Decimal("0.0")
            item["percentage"] = pct
            if row["category__monthly_budget"] and row["category__monthly_budget"] > 0:
                budget_pct = round((row["total"] / row["category__monthly_budget"]) * Decimal("100"), 1)
                item["budget_percentage"] = budget_pct
                item["budget_exceeded"] = row["total"] > row["category__monthly_budget"]
            else:
                item["budget_percentage"] = None
                item["budget_exceeded"] = False
            expense_by_category.append(item)
        else:
            pct = round((row["total"] / total_income) * Decimal("100"), 1) if total_income > 0 else Decimal("0.0")
            item["percentage"] = pct
            income_by_category.append(item)

    # Daily breakdown for Chart.js bar chart
    days_in_month = calendar.monthrange(year, month)[1]
    daily_rows = (
        period_qs.values("date")
        .annotate(
            day_income=Coalesce(
                Sum("amount", filter=Q(category__category_type=Category.CategoryType.INCOME)),
                Decimal("0.00"),
            ),
            day_expense=Coalesce(
                Sum("amount", filter=Q(category__category_type=Category.CategoryType.EXPENSE)),
                Decimal("0.00"),
            ),
        )
        .order_by("date")
    )
    daily_map = {r["date"].day: r for r in daily_rows}
    daily_labels = []
    daily_income_data = []
    daily_expense_data = []

    for d in range(1, days_in_month + 1):
        daily_labels.append(f"{d:02d}")
        entry = daily_map.get(d)
        daily_income_data.append(float(entry["day_income"]) if entry else 0.0)
        daily_expense_data.append(float(entry["day_expense"]) if entry else 0.0)

    return {
        "year": year,
        "month": month,
        "month_name": MONTH_NAMES_ES.get(month, ""),
        "prev_year": prev_year,
        "prev_month": prev_month,
        "next_year": next_year,
        "next_month": next_month,
        "total_income": total_income,
        "total_expense": total_expense,
        "net_balance": net_balance,
        "income_count": totals["income_count"],
        "expense_count": totals["expense_count"],
        "total_movements_count": totals["income_count"] + totals["expense_count"],
        "savings_rate": savings_rate,
        "expense_ratio": expense_ratio,
        "prev_expense": prev_expense,
        "expense_variation_pct": expense_variation_pct,
        "expense_by_category": expense_by_category,
        "income_by_category": income_by_category,
        "chart_expense_labels": [c["name"] for c in expense_by_category],
        "chart_expense_values": [float(c["total"]) for c in expense_by_category],
        "chart_expense_colors": [c["color"] for c in expense_by_category],
        "chart_daily_labels": daily_labels,
        "chart_daily_income": daily_income_data,
        "chart_daily_expense": daily_expense_data,
        "recent_movements": period_qs[:8],
    }
