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
    path('commande-video/', views.commande_video, name='commande_video'),
    path('commande-video/valider/', views.commande_video_submit, name='commande_video_submit'),

    # Commande directe par produit (lien partageable)
    path('commander/<int:pk>/', views.commande_directe, name='commande_directe'),
    path('commander/<int:pk>/valider/', views.commande_directe_submit, name='commande_directe_submit'),

    # Admin
    path('admin-panel/login/', views.admin_login, name='admin_login'),
    path('admin-panel/', views.admin_dashboard, name='admin_dashboard'),
    path('admin-panel/commandes/', views.admin_orders, name='admin_orders'),
    path('admin-panel/commandes/<int:pk>/', views.admin_order_detail, name='admin_order_detail'),
    path('admin-panel/commandes/<int:pk>/statut/', views.admin_update_status, name='admin_update_status'),
    path('admin-panel/commandes/<int:pk>/terminer/', views.admin_mark_order_completed, name='admin_mark_order_completed'),
    path('admin-panel/produits/', views.admin_products, name='admin_products'),
    path('admin-panel/produits/ajouter/', views.admin_product_add, name='admin_product_add'),
    path('admin-panel/produits/<int:pk>/modifier/', views.admin_product_edit, name='admin_product_edit'),
    path('admin-panel/produits/<int:pk>/supprimer/', views.admin_product_delete, name='admin_product_delete'),
    path('admin-panel/logout/', views.admin_logout, name='admin_logout'),

    # Comptabilité & Stock
    path('admin-panel/comptabilite/', views.admin_comptabilite, name='admin_comptabilite'),
    path('admin-panel/stock/', views.admin_stock, name='admin_stock'),
    path('admin-panel/stock/entree/', views.admin_stock_entry, name='admin_stock_entry'),
    path('admin-panel/stock/sortie/', views.admin_stock_exit, name='admin_stock_exit'),
    path('admin-panel/ventes-hors-site/', views.admin_offline_sales, name='admin_offline_sales'),
    path('admin-panel/ventes-hors-site/ajouter/', views.admin_offline_sale_add, name='admin_offline_sale_add'),
    path('admin-panel/depenses/ajouter/', views.admin_expense_add, name='admin_expense_add'),
    path('admin-panel/depenses/<int:pk>/supprimer/', views.admin_expense_delete, name='admin_expense_delete'),
]
