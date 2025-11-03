from django.contrib import admin
from .models import Profile, Category, Product, CartItem, Order, OrderItem

# --- Administration du Profil ---
@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'role', 'phone', 'city', 'country', 'company_name', 'newsletter')
    list_filter = ('role', 'country', 'newsletter')
    search_fields = ('user__username', 'user__email', 'phone', 'company_name', 'city')
    readonly_fields = ('user',)
    
    fieldsets = (
        ('Utilisateur', {
            'fields': ('user', 'role')
        }),
        ('Coordonnées personnelles', {
            'fields': ('phone', 'birth_date', 'address', 'city', 'postal_code', 'country')
        }),
        ('Informations entreprise (Vendeur)', {
            'fields': ('company_name', 'head_office', 'main_categories', 'company_description'),
            'classes': ('collapse',)
        }),
        ('Préférences', {
            'fields': ('newsletter',)
        }),
    )


# --- Administration des Catégories ---
@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'is_active', 'created_at')
    list_filter = ('is_active', 'created_at')
    search_fields = ('name', 'description')
    prepopulated_fields = {'slug': ('name',)}
    list_editable = ('is_active',)


# --- Administration des Produits ---
@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'seller', 'price', 'discount_percentage', 'badge', 'stock', 'is_active', 'is_featured', 'rating', 'created_at')
    list_filter = ('category', 'badge', 'is_active', 'is_featured', 'created_at')
    search_fields = ('name', 'seller__username', 'description')
    list_editable = ('price', 'discount_percentage', 'badge', 'stock', 'is_active', 'is_featured', 'rating')
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        ('Informations de base', {
            'fields': ('seller', 'category', 'name', 'description')
        }),
        ('Prix et réductions', {
            'fields': ('price', 'old_price', 'discount_percentage')
        }),
        ('Images', {
            'fields': ('image', 'image2', 'image3')
        }),
        ('Options d\'affichage', {
            'fields': ('badge', 'rating', 'is_active', 'is_featured')
        }),
        ('Inventaire', {
            'fields': ('stock',)
        }),
        ('Dates', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(seller=request.user)


# --- Administration du Panier ---
@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    list_display = ('user', 'product', 'quantity', 'get_total_price', 'added_at')
    list_filter = ('added_at',)
    search_fields = ('user__username', 'product__name')
    readonly_fields = ('added_at', 'get_total_price')
    
    def get_total_price(self, obj):
        return f"{obj.get_total_price()} FCFA"
    get_total_price.short_description = 'Prix total'


# --- Inline pour les articles de commande ---
class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ('product', 'quantity', 'price', 'get_total_price')
    can_delete = False
    
    def get_total_price(self, obj):
        return f"{obj.get_total_price()} FCFA"
    get_total_price.short_description = 'Total'


# --- Administration des Commandes ---
@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'total_price', 'status', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('user__username', 'shipping_address', 'phone')
    list_editable = ('status',)
    readonly_fields = ('created_at', 'updated_at')
    inlines = [OrderItemInline]
    
    fieldsets = (
        ('Informations client', {
            'fields': ('user', 'phone', 'shipping_address')
        }),
        ('Détails de la commande', {
            'fields': ('total_price', 'status')
        }),
        ('Dates', {
            'fields': ('created_at', 'updated_at')
        }),
    )


# --- Administration des articles de commande ---
@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ('order', 'product', 'quantity', 'price', 'get_total_price')
    list_filter = ('order__created_at',)
    search_fields = ('order__id', 'product__name')
    readonly_fields = ('get_total_price',)
    
    def get_total_price(self, obj):
        return f"{obj.get_total_price()} FCFA"
    get_total_price.short_description = 'Total'


