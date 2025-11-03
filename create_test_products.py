import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from app.models import Product, Category
from django.contrib.auth.models import User

# Récupérer ou créer un vendeur
try:
    vendeur = User.objects.filter(profile__role='vendeur').first()
    if not vendeur:
        # Créer un vendeur de test
        vendeur = User.objects.create_user(
            username='vendeur_test',
            email='vendeur@test.com',
            password='test1234'
        )
        from app.models import Profile
        Profile.objects.create(user=vendeur, role='vendeur')
        print(f"✓ Vendeur de test créé: {vendeur.username}")
    else:
        print(f"✓ Vendeur existant utilisé: {vendeur.username}")
except Exception as e:
    print(f"Erreur vendeur: {e}")
    vendeur = User.objects.first()

# Récupérer quelques catégories
categories = list(Category.objects.all()[:5])

if not categories:
    print("❌ Aucune catégorie trouvée. Exécutez d'abord create_categories.py")
    exit()

# Liste de produits de test
produits = [
    {
        'name': 'Smartphone Samsung Galaxy S24',
        'description': 'Dernier smartphone Samsung avec écran AMOLED, 256GB de stockage',
        'price': 450000,
        'old_price': 520000,
        'discount_percentage': 13,
        'badge': 'new',
        'rating': 4.5,
        'stock': 25,
    },
    {
        'name': 'Canapé 3 places moderne',
        'description': 'Canapé confortable en tissu de qualité, design contemporain',
        'price': 285000,
        'old_price': 350000,
        'discount_percentage': 19,
        'badge': 'featured',
        'rating': 4.8,
        'stock': 10,
    },
    {
        'name': 'Ordinateur Portable Dell XPS 15',
        'description': 'Intel i7, 16GB RAM, 512GB SSD, écran 4K',
        'price': 890000,
        'old_price': 1100000,
        'discount_percentage': 19,
        'badge': 'trending',
        'rating': 4.9,
        'stock': 8,
    },
    {
        'name': 'Table à manger en bois massif',
        'description': 'Table rectangulaire 6 personnes, bois de chêne',
        'price': 175000,
        'stock': 15,
        'rating': 4.3,
    },
    {
        'name': 'Machine à café expresso',
        'description': 'Machine professionnelle pour un café de qualité',
        'price': 65000,
        'old_price': 85000,
        'discount_percentage': 24,
        'badge': 'discount',
        'rating': 4.6,
        'stock': 30,
    },
    {
        'name': 'Armoire 3 portes',
        'description': 'Grande armoire en bois avec miroir central',
        'price': 195000,
        'stock': 12,
        'rating': 4.4,
    },
    {
        'name': 'Écouteurs Bluetooth Premium',
        'description': 'Son haute qualité, réduction de bruit active',
        'price': 45000,
        'old_price': 60000,
        'discount_percentage': 25,
        'badge': 'trending',
        'rating': 4.7,
        'stock': 50,
    },
    {
        'name': 'Téléviseur Smart TV 55 pouces',
        'description': 'TV 4K HDR, système Android TV intégré',
        'price': 425000,
        'old_price': 550000,
        'discount_percentage': 23,
        'badge': 'featured',
        'rating': 4.6,
        'stock': 18,
    },
]

print("\n🚀 Création de produits de test...\n")

created_count = 0
for i, prod_data in enumerate(produits):
    # Assigner une catégorie aléatoire
    category = categories[i % len(categories)]
    
    # Vérifier si le produit existe déjà
    existing = Product.objects.filter(name=prod_data['name']).first()
    if existing:
        print(f"- Existe déjà: {prod_data['name']}")
        continue
    
    # Créer le produit
    product = Product.objects.create(
        seller=vendeur,
        category=category,
        **prod_data
    )
    created_count += 1
    print(f"✓ Créé: {product.name} - {product.price} FCFA (Catégorie: {category.name})")

print(f"\n✅ {created_count} nouveaux produits créés")
print(f"📊 Total: {Product.objects.count()} produits dans la base")
print(f"\n💡 Visitez http://127.0.0.1:8000/shop/ pour voir vos produits !")
