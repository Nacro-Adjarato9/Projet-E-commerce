from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),  #  Django cherche la fonction "index" ici
]
from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),  
    path('shop/', views.shop, name='shop'),
    path('cart/', views.cart, name='cart'),
    path('chechkout/', views.chechkout, name='chechkout'),
    path('Apropos/', views.Apropos, name='Apropos'),
    path('inscription/', views.inscription, name='inscription'),
    path('inscription/', views.inscription, name='inscription'),
    path('add_product/', views.add_product, name='add_product'),
    path('vendeur_dashboard/', views.vendeur_dashboard, name='vendeur_dashboard'),
     path('dashboard/', views.vendeur_dashboard),
    path('admin/', views.admin_dashboard, name='admin_dashboard'),
    path('dashboard/admin/', views.admin_dashboard, name='admin_dashboard'),
    path('produit/ajouter/', views.add_product, name='add_product'),
    
]
