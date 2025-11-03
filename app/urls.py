from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('inscription/', views.inscription, name='inscription'),
    path('shop/', views.shop, name='shop'),
    path('cart/', views.cart, name='cart'),
    path('cart/add/<int:product_id>/', views.add_to_cart, name='add_to_cart'),
    path('cart/remove/<int:item_id>/', views.remove_from_cart, name='remove_from_cart'),
    path('cart/update/<int:item_id>/', views.update_cart_item, name='update_cart_item'),
    path('chechkout/', views.chechkout, name='chechkout'),
    path('checkout/', views.checkout_now, name='checkout'),
    path('Apropos/', views.Apropos, name='Apropos'),
    path('add_product/', views.add_product, name='add_product'),
    path('vendeur_dashboard/', views.vendeur_dashboard, name='vendeur_dashboard'),
    path('admin_dashboard/', views.admin_dashboard, name='admin_dashboard'),
]
