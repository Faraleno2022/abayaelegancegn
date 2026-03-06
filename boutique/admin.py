from django.contrib import admin
from .models import Product, Order, OrderItem


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ('nom_produit', 'prix_unitaire', 'quantite')


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('nom', 'categorie', 'prix', 'stock', 'badge', 'note', 'actif', 'date_ajout')
    list_filter = ('categorie', 'badge', 'actif', 'note')
    search_fields = ('nom', 'description')
    list_editable = ('prix', 'stock', 'actif', 'badge')


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('numero', 'prenom_nom', 'telephone', 'total', 'statut', 'date_commande')
    list_filter = ('statut', 'mode_paiement', 'date_commande')
    search_fields = ('numero', 'prenom_nom', 'telephone', 'email')
    list_editable = ('statut',)
    inlines = [OrderItemInline]
    readonly_fields = ('numero', 'date_commande')
