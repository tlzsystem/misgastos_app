from django.contrib import admin
from .models import Category, Movement


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "user", "category_type", "is_active", "monthly_budget", "created_at")
    list_filter = ("category_type", "is_active", "created_at")
    search_fields = ("name", "description", "user__username", "user__email")
    ordering = ("user", "category_type", "name")


@admin.register(Movement)
class MovementAdmin(admin.ModelAdmin):
    list_display = ("description", "user", "category", "amount", "date", "payment_method")
    list_filter = ("category__category_type", "payment_method", "date")
    search_fields = ("description", "notes", "user__username", "category__name")
    date_hierarchy = "date"
    autocomplete_fields = ()
