from django.contrib import admin
from .models import Medicine,Supplier,Purchase,PurchaseItem,Sale,SaleItem,StockTransaction
from .models import ShopSettings
from .models import UserProfile

admin.site.register(UserProfile)
admin.site.register(
    ShopSettings
)
@admin.register(Supplier)
class SupplierAdmin(admin.ModelAdmin):
    list_display = ('name', 'phone')

@admin.register(Sale)
class SaleAdmin(admin.ModelAdmin):
    list_display = (
        'invoice_number',
        'sale_date',
        'customer_name'
    )


@admin.register(SaleItem)
class SaleItemAdmin(admin.ModelAdmin):
    list_display = (
        'sale',
        'medicine',
        'quantity',
        'selling_price'
    )
@admin.register(Purchase)
class PurchaseAdmin(admin.ModelAdmin):
    list_display = (
        'invoice_number',
        'supplier',
        'purchase_date'
    )


@admin.register(PurchaseItem)
class PurchaseItemAdmin(admin.ModelAdmin):
    list_display = (
        'purchase',
        'medicine',
        'quantity',
        'purchase_price'
    )
@admin.register(Medicine)
class MedicineAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'manufacturer',
        'batch_number',
        'stock_quantity',
        'expiry_date',
        'is_expired',
        'is_in_stock',
        'is_low_stock',
    )

    search_fields = (
        'name',
        'manufacturer',
        'batch_number'
    )

    list_filter = (
        'manufacturer',
        'expiry_date'
    )
@admin.register(StockTransaction)
class StockTransactionAdmin(admin.ModelAdmin):
    list_display = (
        'medicine',
        'transaction_type',
        'quantity',
        'created_at'
    )

    list_filter = (
        'transaction_type',
        'created_at'
    )

    search_fields = (
        'medicine__name',
    )