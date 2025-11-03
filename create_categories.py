import os
import django
from django.utils.text import slugify

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from app.models import Category

# Liste des catégories à créer
categories = [
    {'name': 'Électronique', 'slug': 'electronique', 'description': 'Téléphones, ordinateurs, accessoires électroniques'},
    {'name': 'Mode & Vêtements', 'slug': 'mode-vetements', 'description': 'Vêtements homme, femme, enfant, chaussures, accessoires'},
    {'name': 'Maison & Décoration', 'slug': 'maison-decoration', 'description': 'Meubles, décoration, électroménager'},
    {'name': 'Beauté & Santé', 'slug': 'beaute-sante', 'description': 'Cosmétiques, parfums, soins, produits de santé'},
    {'name': 'Sports & Loisirs', 'slug': 'sports-loisirs', 'description': 'Équipements sportifs, jeux, loisirs créatifs'},
    {'name': 'Alimentation', 'slug': 'alimentation', 'description': 'Produits alimentaires, boissons, épicerie'},
    {'name': 'Livres & Média', 'slug': 'livres-media', 'description': 'Livres, films, musique, jeux vidéo'},
    {'name': 'Jouets & Enfants', 'slug': 'jouets-enfants', 'description': 'Jouets, jeux, articles pour bébés et enfants'},
    {'name': 'Bijoux & Montres', 'slug': 'bijoux-montres', 'description': 'Bijoux, montres, accessoires précieux'},
    {'name': 'Auto & Moto', 'slug': 'auto-moto', 'description': 'Pièces auto, accessoires moto, équipements'},
]

print("🚀 Création des catégories...\n")

created_count = 0
for cat_data in categories:
    cat, created = Category.objects.get_or_create(
        slug=cat_data['slug'],
        defaults={
            'name': cat_data['name'],
            'description': cat_data['description']
        }
    )
    if created:
        created_count += 1
        print(f'✓ Créé: {cat.name}')
    else:
        print(f'- Existe déjà: {cat.name}')

print(f'\n {created_count} nouvelles catégories créées')
print(f' Total: {Category.objects.count()} catégories dans la base')
