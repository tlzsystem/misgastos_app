from datetime import date
from decimal import Decimal
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse

from .models import Category, Movement
from .services import get_monthly_summary

User = get_user_model()


class MultiUserFinancesTests(TestCase):
    def setUp(self):
        self.user_a = User.objects.create_user(
            username="alice",
            email="alice@example.com",
            password="Password123!",
            first_name="Alice",
        )
        self.user_b = User.objects.create_user(
            username="bob",
            email="bob@example.com",
            password="Password123!",
            first_name="Bob",
        )

        # Categorías de Alice
        self.cat_income_a = Category.objects.create(
            user=self.user_a,
            name="Sueldo",
            category_type=Category.CategoryType.INCOME,
            color="#10b981",
            icon="briefcase",
        )
        self.cat_expense_a = Category.objects.create(
            user=self.user_a,
            name="Supermercado",
            category_type=Category.CategoryType.EXPENSE,
            color="#f97316",
            icon="shopping-cart",
            monthly_budget=Decimal("300000.00"),
        )

        # Categorías de Bob
        self.cat_expense_b = Category.objects.create(
            user=self.user_b,
            name="Arriendo Bob",
            category_type=Category.CategoryType.EXPENSE,
            color="#6366f1",
            icon="home",
        )

    def test_category_creation_edit_and_deactivation(self):
        self.client.login(username="alice", password="Password123!")

        # Crear categoría
        resp = self.client.post(
            reverse("finances:category_create"),
            {
                "name": "Transporte",
                "category_type": Category.CategoryType.EXPENSE,
                "color": "#3b82f6",
                "icon": "car",
                "description": "Metro y combustible",
                "is_active": True,
            },
        )
        self.assertEqual(resp.status_code, 302)
        cat = Category.objects.get(user=self.user_a, name="Transporte")
        self.assertTrue(cat.is_active)

        # Editar categoría
        resp_edit = self.client.post(
            reverse("finances:category_update", args=[cat.pk]),
            {
                "name": "Transporte Urbano",
                "category_type": Category.CategoryType.EXPENSE,
                "color": "#3b82f6",
                "icon": "car",
                "description": "Actualizado",
                "is_active": True,
            },
        )
        self.assertEqual(resp_edit.status_code, 302)
        cat.refresh_from_db()
        self.assertEqual(cat.name, "Transporte Urbano")

        # Desactivar categoría
        resp_toggle = self.client.post(
            reverse("finances:category_toggle_active", args=[cat.pk])
        )
        self.assertEqual(resp_toggle.status_code, 302)
        cat.refresh_from_db()
        self.assertFalse(cat.is_active)

    def test_deactivated_category_cannot_be_used_for_new_movement(self):
        self.cat_expense_a.is_active = False
        self.cat_expense_a.save()

        mov = Movement(
            user=self.user_a,
            category=self.cat_expense_a,
            amount=Decimal("15000.00"),
            description="Compra con categoría inactiva",
            date=date(2026, 10, 15),
        )
        with self.assertRaises(ValidationError):
            mov.save()

    def test_movement_crud_and_monthly_summary(self):
        self.client.login(username="alice", password="Password123!")

        # Crear ingreso
        self.client.post(
            reverse("finances:movement_create"),
            {
                "category": self.cat_income_a.pk,
                "amount": "1500000.00",
                "description": "Sueldo Octubre",
                "date": "2026-10-05",
                "payment_method": Movement.PaymentMethod.TRANSFER,
                "notes": "Pago mensual",
            },
        )

        # Crear gasto
        self.client.post(
            reverse("finances:movement_create"),
            {
                "category": self.cat_expense_a.pk,
                "amount": "120000.00",
                "description": "Compra mensual supermercado",
                "date": "2026-10-10",
                "payment_method": Movement.PaymentMethod.DEBIT,
                "notes": "",
            },
        )

        summary = get_monthly_summary(self.user_a, 2026, 10)
        self.assertEqual(summary["total_income"], Decimal("1500000.00"))
        self.assertEqual(summary["total_expense"], Decimal("120000.00"))
        self.assertEqual(summary["net_balance"], Decimal("1380000.00"))

        # Editar gasto
        mov = Movement.objects.get(user=self.user_a, description="Compra mensual supermercado")
        self.client.post(
            reverse("finances:movement_update", args=[mov.pk]),
            {
                "category": self.cat_expense_a.pk,
                "amount": "150000.00",
                "description": "Compra mensual supermercado actualizada",
                "date": "2026-10-10",
                "payment_method": Movement.PaymentMethod.CREDIT,
                "notes": "Con tarjeta",
            },
        )
        mov.refresh_from_db()
        self.assertEqual(mov.amount, Decimal("150000.00"))

        # Eliminar gasto
        self.client.post(reverse("finances:movement_delete", args=[mov.pk]))
        self.assertFalse(Movement.objects.filter(pk=mov.pk).exists())

    def test_multi_user_data_isolation(self):
        mov_b = Movement.objects.create(
            user=self.user_b,
            category=self.cat_expense_b,
            amount=Decimal("450000.00"),
            description="Pago arriendo de Bob",
            date=date(2026, 10, 1),
        )

        # Alice inicia sesión e intenta acceder a los recursos de Bob
        self.client.login(username="alice", password="Password123!")

        # No puede editar categoría de Bob (404)
        resp_cat = self.client.get(
            reverse("finances:category_update", args=[self.cat_expense_b.pk])
        )
        self.assertEqual(resp_cat.status_code, 404)

        # No puede desactivar categoría de Bob (404)
        resp_toggle = self.client.post(
            reverse("finances:category_toggle_active", args=[self.cat_expense_b.pk])
        )
        self.assertEqual(resp_toggle.status_code, 404)

        # No puede editar ni eliminar movimiento de Bob (404)
        resp_mov_edit = self.client.get(
            reverse("finances:movement_update", args=[mov_b.pk])
        )
        self.assertEqual(resp_mov_edit.status_code, 404)

        resp_mov_del = self.client.post(
            reverse("finances:movement_delete", args=[mov_b.pk])
        )
        self.assertEqual(resp_mov_del.status_code, 404)
        self.assertTrue(Movement.objects.filter(pk=mov_b.pk).exists())

        # Alice no puede crear un movimiento usando la categoría de Bob
        cross_mov = Movement(
            user=self.user_a,
            category=self.cat_expense_b,
            amount=Decimal("10000.00"),
            description="Intento cruzado",
            date=date(2026, 10, 12),
        )
        with self.assertRaises(ValidationError):
            cross_mov.save()

    def test_all_views_render_cleanly(self):
        # Vistas públicas
        self.assertEqual(self.client.get(reverse("accounts:login")).status_code, 200)
        self.assertEqual(self.client.get(reverse("accounts:register")).status_code, 200)

        # Vistas autenticadas
        self.client.login(username="alice", password="Password123!")
        mov = Movement.objects.create(
            user=self.user_a,
            category=self.cat_expense_a,
            amount=Decimal("25000.00"),
            description="Gasto de prueba",
            date=date(2026, 10, 18),
        )

        self.assertEqual(self.client.get(reverse("finances:dashboard")).status_code, 200)
        self.assertEqual(self.client.get(reverse("finances:movement_list")).status_code, 200)
        self.assertEqual(self.client.get(reverse("finances:movement_create")).status_code, 200)
        self.assertEqual(
            self.client.get(reverse("finances:movement_update", args=[mov.pk])).status_code,
            200,
        )
        self.assertEqual(
            self.client.get(reverse("finances:movement_delete", args=[mov.pk])).status_code,
            200,
        )
        self.assertEqual(self.client.get(reverse("finances:category_list")).status_code, 200)
        self.assertEqual(self.client.get(reverse("finances:category_create")).status_code, 200)
        self.assertEqual(
            self.client.get(
                reverse("finances:category_update", args=[self.cat_expense_a.pk])
            ).status_code,
            200,
        )
        self.assertEqual(self.client.get(reverse("accounts:profile")).status_code, 200)

