from django.contrib import admin
from .models import Product, CartItem, Order

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'seller', 'price', 'created_at')
    search_fields = ('name', 'seller__username')
    list_filter = ('created_at',)

@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    list_display = ('user', 'product', 'quantity')
    search_fields = ('user__username', 'product__name')

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('user', 'total_price', 'created_at')
    list_filter = ('created_at',)

