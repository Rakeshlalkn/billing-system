from django.contrib import admin
from .models import Product, Denomination, Purchase, PurchaseItem, ChangeDenomination

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('product_id', 'name', 'price', 'available_stock', 'tax_percentage')
    search_fields = ('product_id', 'name')

@admin.register(Denomination)
class DenominationAdmin(admin.ModelAdmin):
    list_display = ('value', 'count_available')

class PurchaseItemInline(admin.TabularInline):
    model = PurchaseItem
    readonly_fields = ('line_total',)
    extra = 0

class ChangeDenominationInline(admin.TabularInline):
    model = ChangeDenomination
    extra = 0

@admin.register(Purchase)
class PurchaseAdmin(admin.ModelAdmin):
    list_display = ('id', 'customer_email', 'created_at', 'total', 'paid_amount', 'balance')
    inlines = [PurchaseItemInline, ChangeDenominationInline]
    readonly_fields = ('created_at',)
