from django.contrib import admin
from .models import Product, Order, OrderItem, OfflineSale, StockMovement, Expense


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ('nom_produit', 'prix_unitaire', 'quantite')


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('nom', 'categorie', 'prix', 'prix_achat', 'stock', 'seuil_alerte_stock', 'badge', 'note', 'actif', 'date_ajout')
    list_filter = ('categorie', 'badge', 'actif', 'note')
    search_fields = ('nom', 'description')
    list_editable = ('prix', 'prix_achat', 'stock', 'seuil_alerte_stock', 'actif', 'badge')


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('numero', 'prenom_nom', 'telephone', 'total', 'statut', 'date_commande')
    list_filter = ('statut', 'mode_paiement', 'date_commande')
    search_fields = ('numero', 'prenom_nom', 'telephone', 'email')
    list_editable = ('statut',)
    inlines = [OrderItemInline]
    readonly_fields = ('numero', 'date_commande')


@admin.register(OfflineSale)
class OfflineSaleAdmin(admin.ModelAdmin):
    list_display = ('nom_produit', 'quantite', 'prix_vente', 'canal', 'client', 'date_vente')
    list_filter = ('canal', 'date_vente')
    search_fields = ('nom_produit', 'client', 'telephone_client', 'notes')
    raw_id_fields = ('produit',)


@admin.register(StockMovement)
class StockMovementAdmin(admin.ModelAdmin):
    list_display = ('produit', 'type_mouvement', 'motif', 'quantite', 'stock_avant', 'stock_apres', 'date')
    list_filter = ('type_mouvement', 'motif', 'date')
    search_fields = ('produit__nom', 'reference', 'notes')
    readonly_fields = ('stock_avant', 'stock_apres')


@admin.register(Expense)
class ExpenseAdmin(admin.ModelAdmin):
    list_display = ('libelle', 'montant', 'categorie', 'date')
    list_filter = ('categorie', 'date')
    search_fields = ('libelle', 'notes')
