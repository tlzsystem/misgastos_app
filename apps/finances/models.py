from decimal import Decimal
from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models
from django.utils import timezone


class CategoryQuerySet(models.QuerySet):
    def for_user(self, user):
        return self.filter(user=user)

    def active(self):
        return self.filter(is_active=True)

    def expenses(self):
        return self.filter(category_type=Category.CategoryType.EXPENSE)

    def incomes(self):
        return self.filter(category_type=Category.CategoryType.INCOME)


class Category(models.Model):
    class CategoryType(models.TextChoices):
        EXPENSE = "EXPENSE", "Gasto"
        INCOME = "INCOME", "Ingreso"

    ICON_CHOICES = [
        ("shopping-cart", "Compras / Supermercado"),
        ("utensils", "Alimentación / Restaurantes"),
        ("home", "Vivienda / Hogar"),
        ("car", "Transporte / Vehículo"),
        ("zap", "Servicios / Cuentas"),
        ("heart-pulse", "Salud / Bienestar"),
        ("film", "Entretenimiento / Ocio"),
        ("graduation-cap", "Educación"),
        ("plane", "Viajes / Vacaciones"),
        ("briefcase", "Sueldo / Trabajo"),
        ("trending-up", "Inversiones / Rendimientos"),
        ("laptop", "Freelance / Proyectos"),
        ("gift", "Regalos / Bonos"),
        ("piggy-bank", "Ahorro"),
        ("credit-card", "Deudas / Tarjetas"),
        ("tag", "General / Otro"),
    ]

    COLOR_CHOICES = [
        ("#6366f1", "Índigo"),
        ("#ec4899", "Rosa"),
        ("#f43f5e", "Coral"),
        ("#f97316", "Naranja"),
        ("#eab308", "Ámbar"),
        ("#10b981", "Esmeralda"),
        ("#14b8a6", "Turquesa"),
        ("#06b6d4", "Cian"),
        ("#3b82f6", "Azul"),
        ("#8b5cf6", "Violeta"),
        ("#64748b", "Pizarra"),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="categories",
        verbose_name="Usuario",
    )
    name = models.CharField("Nombre", max_length=80)
    category_type = models.CharField(
        "Tipo de categoría",
        max_length=10,
        choices=CategoryType.choices,
        default=CategoryType.EXPENSE,
    )
    color = models.CharField(
        "Color identificador",
        max_length=7,
        choices=COLOR_CHOICES,
        default="#6366f1",
    )
    icon = models.CharField(
        "Ícono",
        max_length=40,
        choices=ICON_CHOICES,
        default="tag",
    )
    description = models.CharField(
        "Descripción corta",
        max_length=180,
        blank=True,
    )
    monthly_budget = models.DecimalField(
        "Presupuesto mensual sugerido",
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(Decimal("0.00"))],
        help_text="Opcional: define un tope mensual de referencia para esta categoría.",
    )
    is_active = models.BooleanField(
        "Activa",
        default=True,
        help_text="Si se desactiva, no aparecerá al registrar nuevos movimientos pero conservará su historial.",
    )
    created_at = models.DateTimeField("Creada el", auto_now_add=True)
    updated_at = models.DateTimeField("Actualizada el", auto_now=True)

    objects = CategoryQuerySet.as_manager()

    class Meta:
        verbose_name = "Categoría"
        verbose_name_plural = "Categorías"
        ordering = ["-is_active", "category_type", "name"]
        constraints = [
            models.UniqueConstraint(
                fields=["user", "name", "category_type"],
                name="unique_user_category_name_type",
            )
        ]
        indexes = [
            models.Index(fields=["user", "is_active", "category_type"]),
        ]

    def __str__(self):
        status = "" if self.is_active else " (Inactiva)"
        return f"{self.name} ({self.get_category_type_display()}){status}"

    @property
    def is_expense(self) -> bool:
        return self.category_type == self.CategoryType.EXPENSE

    @property
    def is_income(self) -> bool:
        return self.category_type == self.CategoryType.INCOME


class MovementQuerySet(models.QuerySet):
    def for_user(self, user):
        return self.filter(user=user)

    def for_period(self, year: int, month: int):
        return self.filter(date__year=year, date__month=month)

    def expenses(self):
        return self.filter(category__category_type=Category.CategoryType.EXPENSE)

    def incomes(self):
        return self.filter(category__category_type=Category.CategoryType.INCOME)


class Movement(models.Model):
    class PaymentMethod(models.TextChoices):
        DEBIT = "DEBIT", "Tarjeta de Débito"
        CREDIT = "CREDIT", "Tarjeta de Crédito"
        TRANSFER = "TRANSFER", "Transferencia Bancaria"
        CASH = "CASH", "Efectivo"
        OTHER = "OTHER", "Otro"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="movements",
        verbose_name="Usuario",
    )
    category = models.ForeignKey(
        Category,
        on_delete=models.PROTECT,
        related_name="movements",
        verbose_name="Categoría",
    )
    amount = models.DecimalField(
        "Monto",
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.01"))],
    )
    description = models.CharField(
        "Concepto / Descripción",
        max_length=160,
    )
    notes = models.TextField(
        "Notas adicionales",
        blank=True,
    )
    date = models.DateField(
        "Fecha del movimiento",
        default=timezone.localdate,
        db_index=True,
    )
    payment_method = models.CharField(
        "Medio de pago",
        max_length=20,
        choices=PaymentMethod.choices,
        default=PaymentMethod.DEBIT,
    )
    created_at = models.DateTimeField("Registrado el", auto_now_add=True)
    updated_at = models.DateTimeField("Actualizado el", auto_now=True)

    objects = MovementQuerySet.as_manager()

    class Meta:
        verbose_name = "Movimiento"
        verbose_name_plural = "Movimientos"
        ordering = ["-date", "-created_at", "-id"]
        indexes = [
            models.Index(fields=["user", "date"]),
            models.Index(fields=["user", "category"]),
        ]

    def __str__(self):
        return f"{self.description} - ${self.amount} ({self.date})"

    @property
    def movement_type(self):
        return self.category.category_type

    @property
    def is_expense(self) -> bool:
        return self.category.category_type == Category.CategoryType.EXPENSE

    @property
    def is_income(self) -> bool:
        return self.category.category_type == Category.CategoryType.INCOME

    def clean(self):
        super().clean()
        if self.category_id and self.user_id:
            if self.category.user_id != self.user_id:
                raise ValidationError(
                    {"category": "La categoría seleccionada no pertenece a tu cuenta de usuario."}
                )

            # Verify active status when creating a movement or changing to another category
            is_new = self.pk is None
            category_changed = False
            if not is_new:
                original_category_id = (
                    Movement.objects.filter(pk=self.pk).values_list("category_id", flat=True).first()
                )
                category_changed = original_category_id != self.category_id

            if (is_new or category_changed) and not self.category.is_active:
                raise ValidationError(
                    {
                        "category": (
                            "No puedes asignar una categoría desactivada. "
                            "Actívala primero o selecciona una categoría activa."
                        )
                    }
                )

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)
