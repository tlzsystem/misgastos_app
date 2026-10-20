from datetime import date
from decimal import Decimal
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.finances.models import Category, Movement
from apps.finances.services import seed_default_categories_for_user

User = get_user_model()


class Command(BaseCommand):
    help = "Crea un usuario de demostración con categorías e historial de movimientos del mes actual."

    def handle(self, *args, **options):
        user, created = User.objects.get_or_create(
            username="demo",
            defaults={
                "first_name": "Usuario",
                "last_name": "Demo",
                "email": "demo@misgastos.local",
            },
        )
        if created:
            user.set_password("demo12345")
            user.save()
            self.stdout.write(self.style.SUCCESS("Usuario 'demo' creado (contraseña: demo12345)."))
        else:
            self.stdout.write("El usuario 'demo' ya existe.")

        seed_default_categories_for_user(user)

        if Movement.objects.for_user(user).exists():
            self.stdout.write("El usuario 'demo' ya cuenta con movimientos registrados.")
            return

        today = timezone.localdate()
        year, month = today.year, today.month

        def get_cat(name):
            return Category.objects.filter(user=user, name__icontains=name).first()

        sample_movements = [
            (get_cat("Sueldo"), Decimal("1850000"), "Sueldo mensual depositado", 1, Movement.PaymentMethod.TRANSFER),
            (get_cat("Freelance"), Decimal("320000"), "Proyecto consultoría web", 5, Movement.PaymentMethod.TRANSFER),
            (get_cat("Vivienda"), Decimal("520000"), "Pago arriendo y gastos comunes", 2, Movement.PaymentMethod.TRANSFER),
            (get_cat("Supermercado"), Decimal("165000"), "Compra mensual supermercado", 4, Movement.PaymentMethod.DEBIT),
            (get_cat("Servicios"), Decimal("78500"), "Luz, agua e internet fibra", 7, Movement.PaymentMethod.DEBIT),
            (get_cat("Transporte"), Decimal("54000"), "Carga combustible y TAG", 9, Movement.PaymentMethod.CREDIT),
            (get_cat("Restaurantes"), Decimal("42000"), "Cena fin de semana", 12, Movement.PaymentMethod.CREDIT),
            (get_cat("Salud"), Decimal("35000"), "Farmacia y control médico", 14, Movement.PaymentMethod.DEBIT),
            (get_cat("Entretenimiento"), Decimal("24900"), "Suscripciones streaming y música", 15, Movement.PaymentMethod.CREDIT),
        ]

        for cat, amount, desc, day_num, method in sample_movements:
            if cat:
                safe_day = min(day_num, 28)
                Movement.objects.create(
                    user=user,
                    category=cat,
                    amount=amount,
                    description=desc,
                    date=date(year, month, safe_day),
                    payment_method=method,
                )

        self.stdout.write(
            self.style.SUCCESS("Datos de demostración cargados exitosamente para el usuario 'demo'.")
        )
