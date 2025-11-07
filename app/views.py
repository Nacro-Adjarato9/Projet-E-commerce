from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, logout
from django.contrib import messages
from django.http import HttpResponse

from .models import Product
from .models import CartItem, Order, OrderItem
from django.views.decorators.cache import cache_page
from django.shortcuts import get_object_or_404
from django.db.models import F, Sum
from .forms import RegistrationForm, LoginForm, ProductForm


def index(request):
    return render(request, 'index.html')


def login_view(request):
    """Vue de connexion. Redirige selon le rôle après login."""
    if request.user.is_authenticated:
        # Déjà connecté, rediriger selon rôle
        if hasattr(request.user, 'profile') and request.user.profile.role == 'vendeur':
            return redirect('vendeur_dashboard')
        return redirect('index')
    
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            user = form.cleaned_data['user']
            
            # AVANT de connecter : récupérer le panier session
            session_cart = request.session.get('cart', {})
            
            login(request, user)
            
            # APRÈS connexion : transférer le panier session vers la BD
            if session_cart:
                for product_id, quantity in session_cart.items():
                    try:
                        product = Product.objects.get(pk=int(product_id), is_active=True)
                        cart_item, created = CartItem.objects.get_or_create(
                            user=user,
                            product=product
                        )
                        if not created:
                            # Additionner les quantités
                            cart_item.quantity = F('quantity') + quantity
                            cart_item.save(update_fields=['quantity'])
                        else:
                            cart_item.quantity = quantity
                            cart_item.save(update_fields=['quantity'])
                    except Product.DoesNotExist:
                        pass
                
                # Vider le panier session
                request.session['cart'] = {}
                request.session.modified = True
                messages.info(request, "Votre panier a été transféré avec succès.")
            
            # Créer un profil si n'existe pas (cas superuser)
            if not hasattr(user, 'profile'):
                from .models import Profile
                Profile.objects.create(user=user, role='client')
            
            # Rediriger selon le rôle
            if hasattr(user, 'profile') and user.profile.role == 'vendeur':
                messages.success(request, f"Bienvenue {user.username} ! Gérez votre boutique.")
                return redirect('vendeur_dashboard')
            else:
                messages.success(request, f"Bienvenue {user.username} !")
                return redirect('index')
        else:
            messages.error(request, "Erreur de connexion. Vérifiez vos identifiants.")
    else:
        form = LoginForm()
    
    return render(request, 'login.html', {'form': form})


def logout_view(request):
    """Déconnexion"""
    logout(request)
    messages.success(request, "Vous êtes déconnecté.")
    return redirect('index')


@cache_page(60)
def shop(request):
    """Affiche tous les produits actifs dans la boutique, avec pagination."""
    from django.core.paginator import Paginator
    from .models import Category

    qs = Product.objects.filter(is_active=True).select_related('seller', 'category').order_by('-created_at')

    # Filtrer par catégorie si spécifié
    category_id = request.GET.get('category')
    if category_id:
        qs = qs.filter(category_id=category_id)

    # Tri
    sort_by = request.GET.get('sort', '-created_at')
    if sort_by == 'price_asc':
        qs = qs.order_by('price')
    elif sort_by == 'price_desc':
        qs = qs.order_by('-price')
    elif sort_by == 'name':
        qs = qs.order_by('name')
    elif sort_by == 'rating':
        qs = qs.order_by('-rating')
    else:
        qs = qs.order_by('-created_at')

    # Pagination (9 produits par page)
    page_number = request.GET.get('page', 1)
    paginator = Paginator(qs, 9)
    products = paginator.get_page(page_number)

    # Récupérer toutes les catégories actives
    categories = Category.objects.filter(is_active=True).order_by('name')

    context = {
        'products': products,  # Page object
        'paginator': paginator,
        'total_count': paginator.count,
        'categories': categories,
        'current_category': category_id,
        'current_sort': sort_by,
    }
    return render(request, 'shop.html', context)

def cart(request):
    """Affiche le panier - base de données pour utilisateurs connectés, session pour les autres"""
    items = []
    subtotal = 0
    
    if request.user.is_authenticated:
        # Utilisateur connecté : récupérer depuis la base de données
        items = (CartItem.objects
                 .filter(user=request.user)
                 .select_related('product'))
        subtotal = sum([item.get_total_price() for item in items])
    else:
        # Utilisateur non connecté : utiliser la session temporairement
        cart_data = request.session.get('cart', {})
        for product_id, quantity in cart_data.items():
            try:
                product = Product.objects.get(pk=product_id, is_active=True)
                # Créer un objet temporaire (non sauvegardé en BD)
                # Utiliser product.id comme identifiant temporaire
                class TempCartItem:
                    def __init__(self, prod, qty):
                        self.id = prod.id  # ID du produit pour les formulaires
                        self.product = prod
                        self.quantity = qty
                    
                    def get_total_price(self):
                        return self.product.price * self.quantity
                
                temp_item = TempCartItem(product, quantity)
                items.append(temp_item)
                subtotal += product.price * quantity
            except Product.DoesNotExist:
                pass
    
    context = {
        'items': items,
        'subtotal': subtotal,
        'is_authenticated': request.user.is_authenticated,
    }
    return render(request, 'cart.html', context)


def add_to_cart(request, product_id: int):
    """Ajoute un produit au panier - BD pour connectés, session sinon"""
    product = get_object_or_404(Product, pk=product_id, is_active=True)
    
    if request.user.is_authenticated:
        # Utilisateur connecté : enregistrer directement dans la base de données
        cart_item, created = CartItem.objects.get_or_create(
            user=request.user, 
            product=product
        )
        if not created:
            cart_item.quantity = F('quantity') + 1
            cart_item.save(update_fields=['quantity'])
            cart_item.refresh_from_db()
        messages.success(request, f"'{product.name}' ajouté au panier (BD).")
    else:
        # Utilisateur non connecté : stocker dans la session
        cart = request.session.get('cart', {})
        product_id_str = str(product_id)
        
        if product_id_str in cart:
            cart[product_id_str] += 1
        else:
            cart[product_id_str] = 1
        
        request.session['cart'] = cart
        request.session.modified = True
        messages.success(request, f"'{product.name}' ajouté au panier (session). Connectez-vous pour sauvegarder.")
    
    return redirect('cart')


def remove_from_cart(request, item_id: int):
    """Retire un article du panier"""
    if request.user.is_authenticated:
        # Utilisateur connecté : supprimer de la BD
        item = get_object_or_404(CartItem, pk=item_id, user=request.user)
        item.delete()
        messages.success(request, "Article retiré du panier.")
    else:
        # Utilisateur non connecté : retirer de la session
        cart = request.session.get('cart', {})
        product_id_str = str(item_id)
        if product_id_str in cart:
            del cart[product_id_str]
            request.session['cart'] = cart
            request.session.modified = True
            messages.success(request, "Article retiré du panier.")
    
    return redirect('cart')


def update_cart_item(request, item_id: int):
    """Met à jour la quantité d'un article du panier"""
    action = request.POST.get('action')
    qty = request.POST.get('quantity')
    
    if request.user.is_authenticated:
        # Utilisateur connecté : mise à jour BD
        item = get_object_or_404(CartItem, pk=item_id, user=request.user)
        
        if action == 'inc':
            item.quantity = F('quantity') + 1
            item.save(update_fields=['quantity'])
            item.refresh_from_db()
        elif action == 'dec':
            if item.quantity > 1:
                item.quantity = F('quantity') - 1
                item.save(update_fields=['quantity'])
                item.refresh_from_db()
            else:
                item.delete()
                messages.info(request, "Article retiré (quantité 0).")
                return redirect('cart')
        elif qty is not None:
            try:
                q = int(qty)
                if q <= 0:
                    item.delete()
                    messages.info(request, "Article retiré (quantité 0).")
                    return redirect('cart')
                item.quantity = q
                item.save(update_fields=['quantity'])
            except ValueError:
                messages.error(request, "Quantité invalide.")
    else:
        # Utilisateur non connecté : mise à jour session
        cart = request.session.get('cart', {})
        product_id_str = str(item_id)
        
        if product_id_str in cart:
            if action == 'inc':
                cart[product_id_str] += 1
            elif action == 'dec':
                if cart[product_id_str] > 1:
                    cart[product_id_str] -= 1
                else:
                    del cart[product_id_str]
                    messages.info(request, "Article retiré (quantité 0).")
            elif qty is not None:
                try:
                    q = int(qty)
                    if q <= 0:
                        del cart[product_id_str]
                        messages.info(request, "Article retiré (quantité 0).")
                    else:
                        cart[product_id_str] = q
                except ValueError:
                    messages.error(request, "Quantité invalide.")
            
            request.session['cart'] = cart
            request.session.modified = True
    
    return redirect('cart')

def inscription(request):
    """Affiche et traite le formulaire d'inscription.

    Sauvegarde les données dans User + Profile, visibles dans l'admin.
    """
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(request, "Compte créé avec succès. Vous pouvez vous connecter.")
            return redirect('login')  # Redirige vers la page de connexion
        else:
            # Erreurs de validation -> rester sur la page avec messages
            messages.error(request, "Veuillez corriger les erreurs ci-dessous.")
    else:
        form = RegistrationForm()

    return render(request, 'inscription.html', {"form": form})

def Apropos(request):
    return render(request, 'Apropos.html')

def chechkout(request):
    return render(request, 'chechkout.html')


@login_required
def checkout_now(request):
    # Crée une commande à partir du panier courant, puis vide le panier.
    items = (CartItem.objects
             .filter(user=request.user)
             .select_related('product'))
    if not items.exists():
        messages.info(request, "Votre panier est vide.")
        return redirect('cart')

    subtotal = sum([item.get_total_price() for item in items])

    # Récupérer des infos d'adresse basiques (si disponibles)
    shipping_address = ""
    phone = ""
    if hasattr(request.user, 'profile'):
        p = request.user.profile
        shipping_address = p.address or ""
        phone = p.phone or ""

    order = Order.objects.create(
        user=request.user,
        total_price=subtotal,
        shipping_address=shipping_address,
        phone=phone,
    )

    bulk_items = []
    for ci in items:
        bulk_items.append(OrderItem(
            order=order,
            product=ci.product,
            quantity=ci.quantity,
            price=ci.product.price,
        ))
        # Optionnel: décrémenter le stock si nécessaire
        # ci.product.stock = F('stock') - ci.quantity
        # ci.product.save(update_fields=['stock'])

    OrderItem.objects.bulk_create(bulk_items)
    items.delete()

    messages.success(request, f"Commande #{order.id} créée avec succès.")
    return redirect('index')


@login_required
def add_product(request):
    """Formulaire d'ajout de produit - réservé aux vendeurs"""
    # Vérifier que l'utilisateur est un vendeur
    if not hasattr(request.user, 'profile') or request.user.profile.role != 'vendeur':
        messages.error(request, "Vous devez être vendeur pour accéder à cette page.")
        return redirect('index')
    
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES)
        if form.is_valid():
            product = form.save(commit=False)
            product.seller = request.user
            product.save()
            messages.success(request, f"Le produit '{product.name}' a été ajouté avec succès !")
            return redirect('vendeur_dashboard')
        else:
            messages.error(request, "Veuillez corriger les erreurs dans le formulaire.")
    else:
        form = ProductForm()

    return render(request, 'add_product.html', {'form': form})


@login_required
def vendeur_dashboard(request):
    """Dashboard du vendeur avec ses produits"""
    # Créer un profil si n'existe pas
    if not hasattr(request.user, 'profile'):
        from .models import Profile
        Profile.objects.create(user=request.user, role='vendeur')
    
    profile = request.user.profile
    if profile.role != 'vendeur':
        messages.error(request, "Vous n'êtes pas un vendeur.")
        return redirect('index')

    products = Product.objects.filter(seller=request.user).order_by('-created_at')
    
    # Récupérer les commandes liées aux produits du vendeur
    from .models import Order
    orders = Order.objects.filter(items__product__seller=request.user).distinct().order_by('-created_at')
    
    return render(request, 'vendeur_dashboard.html', {
        'products': products,
        'orders': orders
    })


@login_required
def admin_dashboard(request):
    """Dashboard admin"""
    if not request.user.is_staff:
        messages.error(request, "Accès non autorisé.")
        return redirect('index')
    return render(request, 'admin_dashboard.html')


def boutique(request):
    produits = Product.objects.all()
    return render(request, 'shop.html', {'produits': produits})
