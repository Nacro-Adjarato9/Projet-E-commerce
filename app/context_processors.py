"""
Context processors pour rendre des variables disponibles dans tous les templates.
"""
from .models import CartItem


def cart_count(request):
    """
    Renvoie le nombre total d'articles dans le panier de l'utilisateur connecté.
    """
    count = 0
    if request.user.is_authenticated:
        count = CartItem.objects.filter(user=request.user).count()
    return {'cart_count': count}
