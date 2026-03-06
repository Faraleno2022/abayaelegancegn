from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('produit/<int:pk>/', views.product_detail, name='product_detail'),
    path('a-propos/', views.about, name='about'),
    path('panier/', views.cart_view, name='cart'),
    path('panier/ajouter/<int:pk>/', views.add_to_cart, name='add_to_cart'),
    path('panier/modifier/<int:pk>/', views.update_cart, name='update_cart'),
    path('commander/', views.checkout, name='checkout'),
    path('confirmation/<str:numero>/', views.order_confirmation, name='order_confirmation'),
    path('api/cart-count/', views.cart_count, name='cart_count'),

    # Commande en ligne (lien partageable)
    path('commander-en-ligne/', views.commander_en_ligne, name='commander_en_ligne'),
    path('commander-en-ligne/valider/', views.commander_en_ligne_submit, name='commander_en_ligne_submit'),

    # Commande directe par produit (lien partageable)
    path('commander/<int:pk>/', views.commande_directe, name='commande_directe'),
    path('commander/<int:pk>/valider/', views.commande_directe_submit, name='commande_directe_submit'),

    # Admin
    path('admin-panel/login/', views.admin_login, name='admin_login'),
    path('admin-panel/', views.admin_dashboard, name='admin_dashboard'),
    path('admin-panel/commandes/', views.admin_orders, name='admin_orders'),
    path('admin-panel/commandes/<int:pk>/', views.admin_order_detail, name='admin_order_detail'),
    path('admin-panel/commandes/<int:pk>/statut/', views.admin_update_status, name='admin_update_status'),
    path('admin-panel/produits/', views.admin_products, name='admin_products'),
    path('admin-panel/produits/ajouter/', views.admin_product_add, name='admin_product_add'),
    path('admin-panel/produits/<int:pk>/modifier/', views.admin_product_edit, name='admin_product_edit'),
    path('admin-panel/produits/<int:pk>/supprimer/', views.admin_product_delete, name='admin_product_delete'),
    path('admin-panel/logout/', views.admin_logout, name='admin_logout'),
]
