from django.db import models
from django.contrib.auth.models import User

# --- Profil pour gérer le rôle utilisateur ---
class Profile(models.Model):
    ROLE_CHOICES = (
        ('vendeur', 'Vendeur'),
        ('client', 'Client'),
    )

    # Lien avec l'utilisateur core
    user = models.OneToOneField(User, on_delete=models.CASCADE)

    # Rôle
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='client')

    # Infos personnelles
    phone = models.CharField(max_length=30, blank=True, verbose_name="Téléphone")
    birth_date = models.DateField(null=True, blank=True, verbose_name="Date de naissance")
    address = models.TextField(blank=True, verbose_name="Adresse")
    city = models.CharField(max_length=120, blank=True, verbose_name="Ville")
    postal_code = models.CharField(max_length=20, blank=True, verbose_name="Code postal")
    country = models.CharField(max_length=120, blank=True, verbose_name="Pays")

    # Infos entreprise (pour vendeur)
    company_name = models.CharField(max_length=255, blank=True, verbose_name="Nom de l'entreprise")
    head_office = models.CharField(max_length=255, blank=True, verbose_name="Siège")
    main_categories = models.CharField(max_length=255, blank=True, verbose_name="Catégories principales")
    company_description = models.TextField(blank=True, verbose_name="Description de l'entreprise")

    # Consentements
    newsletter = models.BooleanField(default=False, verbose_name="Abonné à la newsletter")

    def __str__(self):
        return f"{self.user.username} - {self.role}"
    
    class Meta:
        verbose_name = "Profil"
        verbose_name_plural = "Profils"


# --- Catégorie de produit ---
class Category(models.Model):
    name = models.CharField(max_length=100, verbose_name="Nom de la catégorie")
    slug = models.SlugField(max_length=100, unique=True)
    description = models.TextField(blank=True, verbose_name="Description")
    image = models.ImageField(upload_to='categories/', blank=True, null=True, verbose_name="Image")
    is_active = models.BooleanField(default=True, verbose_name="Actif")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name = "Catégorie"
        verbose_name_plural = "Catégories"
        ordering = ['name']


# --- Modèle Produit ---
class Product(models.Model):
    BADGE_CHOICES = (
        ('', 'Aucun'),
        ('trending', 'Trending'),
        ('featured', 'Featured'),
        ('new', 'Nouveau'),
        ('discount', 'Réduction'),
    )
    
    seller = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Vendeur")
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Catégorie")
    name = models.CharField(max_length=255, verbose_name="Nom du produit")
    description = models.TextField(blank=True, verbose_name="Description")
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Prix")
    old_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, verbose_name="Ancien prix")
    discount_percentage = models.IntegerField(default=0, verbose_name="Pourcentage de réduction")
    image = models.ImageField(upload_to='products/', blank=True, null=True, verbose_name="Image principale")
    image2 = models.ImageField(upload_to='products/', blank=True, null=True, verbose_name="Image 2")
    image3 = models.ImageField(upload_to='products/', blank=True, null=True, verbose_name="Image 3")
    badge = models.CharField(max_length=20, choices=BADGE_CHOICES, blank=True, verbose_name="Badge")
    rating = models.DecimalField(max_digits=3, decimal_places=1, default=0.0, verbose_name="Note")
    stock = models.PositiveIntegerField(default=0, verbose_name="Stock disponible")
    is_active = models.BooleanField(default=True, verbose_name="Actif")
    is_featured = models.BooleanField(default=False, verbose_name="Mis en avant")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Date de création")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Dernière modification")

    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name = "Produit"
        verbose_name_plural = "Produits"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['is_active', 'created_at']),
            models.Index(fields=['category', 'is_active']),
            models.Index(fields=['created_at']),
        ]


# --- Élément du panier ---
class CartItem(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Utilisateur")
    product = models.ForeignKey(Product, on_delete=models.CASCADE, verbose_name="Produit")
    quantity = models.PositiveIntegerField(default=1, verbose_name="Quantité")
    added_at = models.DateTimeField(auto_now_add=True, verbose_name="Ajouté le")

    def __str__(self):
        return f"{self.user.username} - {self.product.name} x {self.quantity}"
    
    def get_total_price(self):
        return self.product.price * self.quantity
    
    class Meta:
        verbose_name = "Article du panier"
        verbose_name_plural = "Articles du panier"


# --- Commande ---
class Order(models.Model):
    STATUS_CHOICES = (
        ('pending', 'En attente'),
        ('processing', 'En cours'),
        ('shipped', 'Expédié'),
        ('delivered', 'Livré'),
        ('cancelled', 'Annulé'),
    )
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Client")
    total_price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Prix total")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', verbose_name="Statut")
    shipping_address = models.TextField(blank=True, verbose_name="Adresse de livraison")
    phone = models.CharField(max_length=20, blank=True, verbose_name="Téléphone")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Date de commande")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Dernière modification")

    def __str__(self):
        return f"Commande #{self.id} - {self.user.username}"
    
    class Meta:
        verbose_name = "Commande"
        verbose_name_plural = "Commandes"
        ordering = ['-created_at']


# --- Détails de commande ---
class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items', verbose_name="Commande")
    product = models.ForeignKey(Product, on_delete=models.CASCADE, verbose_name="Produit")
    quantity = models.PositiveIntegerField(default=1, verbose_name="Quantité")
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Prix unitaire")

    def __str__(self):
        return f"{self.product.name} x {self.quantity}"
    
    def get_total_price(self):
        return self.price * self.quantity
    
    class Meta:
        verbose_name = "Article de commande"
        verbose_name_plural = "Articles de commande"
