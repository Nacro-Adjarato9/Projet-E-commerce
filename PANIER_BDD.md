# 🛒 Système de Panier avec Base de Données

## 📋 Vue d'ensemble

Le panier utilise maintenant **la base de données** pour persister les données des utilisateurs connectés, avec un système de session temporaire pour les visiteurs non connectés.

## ✅ Fonctionnalités implémentées

### 1. **Utilisateurs Connectés** 
- ✅ Panier enregistré dans la table `CartItem` de la base de données
- ✅ Persistance des données entre les sessions
- ✅ Synchronisation automatique
- ✅ Récupération rapide avec `select_related('product')`

### 2. **Utilisateurs Non Connectés**
- ✅ Panier temporaire dans la session Django
- ✅ Pas de connexion requise pour ajouter au panier
- ✅ Transfert automatique vers la BD lors de la connexion

### 3. **Transfert Automatique**
Lors de la connexion, le panier session est automatiquement transféré vers la base de données :
```python
# Dans login_view()
session_cart = request.session.get('cart', {})
for product_id, quantity in session_cart.items():
    CartItem.objects.get_or_create(user=user, product=product)
```

## 🗂️ Modèle de Base de Données

### Table `CartItem`
```python
class CartItem(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    added_at = models.DateTimeField(auto_now_add=True)
    
    def get_total_price(self):
        return self.product.price * self.quantity
```

### Champs :
- **user** : Utilisateur propriétaire du panier
- **product** : Produit ajouté
- **quantity** : Quantité du produit
- **added_at** : Date d'ajout (timestamp)

## 🔄 Flux de Fonctionnement

### Ajouter au Panier
```
1. Utilisateur clique "Ajouter au panier"
2. Vérification : connecté ou non ?
   
   → Connecté :
     - Recherche CartItem existant (user + product)
     - Si existe : quantity += 1
     - Sinon : Créer nouveau CartItem
     - Sauvegarde dans BD
     
   → Non connecté :
     - Stockage dans request.session['cart']
     - Format : {'product_id': quantity}
     - Message : "Connectez-vous pour sauvegarder"
```

### Afficher le Panier
```
1. Accès à /cart/
2. Vérification : connecté ou non ?
   
   → Connecté :
     - Query : CartItem.objects.filter(user=request.user)
     - Récupération depuis BD
     
   → Non connecté :
     - Lecture de session['cart']
     - Création d'objets temporaires
     - Pas de sauvegarde BD
```

### Connexion avec Panier Session
```
1. Utilisateur se connecte
2. Récupération session_cart
3. Pour chaque produit dans session :
   - Recherche CartItem en BD
   - Si existe : additionner quantités
   - Sinon : créer nouveau
4. Vider session['cart']
5. Message : "Panier transféré avec succès"
```

## 📊 Avantages du Système

### Pour les Utilisateurs Connectés :
✅ **Persistance** : Le panier est sauvegardé même après fermeture du navigateur
✅ **Multi-appareils** : Accès au panier depuis n'importe quel appareil
✅ **Historique** : Champ `added_at` pour tracking
✅ **Sécurité** : Données protégées par authentification

### Pour les Visiteurs :
✅ **Pas de barrière** : Peut ajouter au panier sans compte
✅ **Expérience fluide** : Pas de perte lors de la connexion
✅ **Conversion** : Incitation à créer un compte pour sauvegarder

### Pour l'Administration :
✅ **Analyse** : Voir les paniers abandonnés dans l'admin Django
✅ **Marketing** : Relancer les clients avec paniers non validés
✅ **Statistiques** : Produits les plus ajoutés au panier

## 🔍 Visualisation dans l'Admin Django

Accédez à `/admin/app/cartitem/` pour voir :
- Tous les paniers en base de données
- Utilisateurs avec panier actif
- Produits dans chaque panier
- Quantités et totaux

## 🚀 Utilisation

### Ajouter un Produit au Panier
```python
# URL : /cart/add/<product_id>/
# Méthode : GET (automatique depuis le template)

# Exemple dans template :
<a href="{% url 'add_to_cart' product.id %}">Ajouter au panier</a>
```

### Voir le Panier
```python
# URL : /cart/
# Méthode : GET

# Variables disponibles dans template :
- items : Liste des CartItem (BD) ou objets temporaires (session)
- subtotal : Total du panier
- is_authenticated : Booléen pour affichage conditionnel
```

### Modifier Quantité
```python
# URL : /cart/update/<item_id>/
# Méthode : POST

# Actions disponibles :
- action=inc : Augmenter de 1
- action=dec : Diminuer de 1 (supprime si = 0)
- quantity=X : Définir quantité exacte
```

### Retirer du Panier
```python
# URL : /cart/remove/<item_id>/
# Méthode : POST

# Suppression de la BD ou de la session
```

## 📝 Exemples de Code

### Vérifier si Utilisateur a un Panier
```python
from app.models import CartItem

# Nombre d'items dans le panier
cart_count = CartItem.objects.filter(user=request.user).count()

# Total du panier
from django.db.models import Sum, F
total = CartItem.objects.filter(user=request.user).aggregate(
    total=Sum(F('quantity') * F('product__price'))
)['total'] or 0
```

### Vider le Panier (après commande)
```python
# Supprimer tous les items du panier
CartItem.objects.filter(user=request.user).delete()

# Ou dans checkout_now() (déjà implémenté) :
items.delete()  # Vide après création commande
```

## 🛠️ Maintenance

### Nettoyer les Paniers Anciens (optionnel)
```python
# Script pour supprimer paniers > 30 jours
from datetime import timedelta
from django.utils import timezone
from app.models import CartItem

old_date = timezone.now() - timedelta(days=30)
CartItem.objects.filter(added_at__lt=old_date).delete()
```

### Migrer Données Session → BD (si besoin)
Les données session sont automatiquement transférées lors de la connexion via `login_view()`.

## 📱 Support Mobile/Desktop

Le système fonctionne sur tous les appareils :
- **Desktop** : Expérience complète
- **Mobile** : Interface responsive
- **Tablette** : Optimisé avec CSS glassmorphism

## 🎯 Prochaines Améliorations Possibles

1. **Wishlist** : Liste de souhaits séparée
2. **Panier Sauvegardé** : Plusieurs paniers par utilisateur
3. **Comparaison** : Comparer plusieurs produits
4. **Notifications** : Alertes quand stock disponible
5. **Promo Auto** : Appliquer codes promo automatiques
6. **Export** : Télécharger panier en PDF

## ✅ Tests Recommandés

### Test 1 : Utilisateur Connecté
1. Se connecter
2. Ajouter produit au panier
3. Vérifier dans Admin Django → CartItem
4. Fermer navigateur
5. Se reconnecter → panier toujours là ✅

### Test 2 : Utilisateur Non Connecté
1. Mode navigation privée
2. Ajouter produit au panier
3. Panier visible avec message session
4. Se connecter
5. Panier transféré automatiquement ✅

### Test 3 : Modification Quantité
1. Ajouter produit
2. Augmenter quantité (+)
3. Diminuer quantité (-)
4. Mettre quantité à 0 → suppression ✅

### Test 4 : Commande
1. Panier avec plusieurs produits
2. Cliquer "Commander"
3. Vérifier Order créé
4. Vérifier panier vidé ✅

## 🐛 Débogage

### Vérifier Panier BD
```bash
python manage.py shell
>>> from app.models import CartItem
>>> CartItem.objects.all()
>>> CartItem.objects.filter(user__username='votre_username')
```

### Vérifier Session
```python
# Dans view
print(request.session.get('cart', {}))
```

### Réinitialiser Panier
```bash
python manage.py shell
>>> from app.models import CartItem
>>> CartItem.objects.all().delete()
```

## 📞 Support

Pour toute question :
- Vérifier la console Django pour les erreurs
- Consulter `/admin/app/cartitem/` pour l'état du panier
- Vérifier les messages Django dans le template

---

**Mis à jour le** : 7 novembre 2025  
**Version** : 2.0 (Base de données + Session)  
**Auteur** : Système de Panier E-commerce Django
