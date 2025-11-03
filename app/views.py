from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Product
from django.http import HttpResponse

# Create your views here.
from django.shortcuts import render
from django.contrib.auth.decorators import login_required


def index(request):
    return render(request, 'index.html')

def shop(request):
    return render(request,'shop.html' )

def cart(request):
    return render(request, 'cart.html')

def inscription(request):
    return render(request, 'inscription.html')

def Apropos(request):
    return render(request, 'Apropos.html')

def chechkout(request):
    return render(request, 'chechkout.html')

def add_product(request):
    return render(request, 'add_product.html')

@login_required
def vendeur_dashboard(request):
    if request.user.role == 'vendeur':
        return render(request, 'app/vendeur_dashboard.html')
    return render(request, 'app/forbidden.html')

@login_required
def vendeur_dashboard(request):
    profile = request.user.profile
    if profile.role != 'vendeur':
        return HttpResponse("Vous n'êtes pas un vendeur.")

    products = Product.objects.filter(seller=request.user)
    return render(request, 'app/vendeur_dashboard.html', {'products': products})

@login_required
def admin_dashboard(request):
    if request.user.role == 'admin':
        return render(request, 'app/admin_dashboard.html')
    
    return render(request, 'app/forbidden.html')


@login_required
def add_product(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        description = request.POST.get('description')
        price = request.POST.get('price')

        if name and price:
            Product.objects.create(
                vendeur=request.user,
                name=name,
                description=description,
                price=price
            )
            messages.success(request, " Votre produit a été ajouté avec succès !")
            return redirect('add_product')  # redirection vers la même page
        else:
            messages.error(request, " Veuillez remplir tous les champs obligatoires.")

    return render(request, 'add_product.html')

# views.py
def boutique(request):
    produits = produits.objects.filter(est_actif=True).order_by('-date_ajout')
    return render(request, 'shop.html', {'produits': produits})

def boutique(request):
    produits = produits.objects.all()  # récupère tous les produits mis en ligne
    return render(request, 'shop.html', {'produits': produits})
