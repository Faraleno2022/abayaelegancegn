from django.db import models
from django.utils import timezone
import uuid


class Product(models.Model):
    CATEGORY_CHOICES = [
        ('mode', 'Mode'),
        ('accessoires', 'Accessoires'),
        ('maison', 'Maison'),
    ]
    BADGE_CHOICES = [
        ('', 'Aucun'),
        ('Nouveau', 'Nouveau'),
        ('Bestseller', 'Bestseller'),
        ('Exclusif', 'Exclusif'),
        ('Premium', 'Premium'),
    ]

    nom = models.CharField(max_length=200)
    categorie = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    prix = models.DecimalField(max_digits=12, decimal_places=0)
    description = models.TextField()
    image = models.ImageField(upload_to='produits/', blank=True, null=True)
    image_url = models.URLField(blank=True, null=True, help_text="URL externe de l'image (si pas d'upload)")
    badge = models.CharField(max_length=20, choices=BADGE_CHOICES, blank=True, default='')
    note = models.IntegerField(default=5, choices=[(i, f'{i} étoile(s)') for i in range(1, 6)])
    stock = models.IntegerField(default=10)
    prix_achat = models.DecimalField(
        max_digits=12, decimal_places=0, default=0,
        verbose_name="Prix d'achat", help_text="Prix d'achat en GNF (pour calcul du bénéfice)"
    )
    seuil_alerte_stock = models.IntegerField(
        default=3, verbose_name="Seuil alerte stock",
        help_text="Alerte si le stock descend en dessous de ce seuil"
    )
    date_ajout = models.DateTimeField(auto_now_add=True)
    actif = models.BooleanField(default=True)

    class Meta:
        ordering = ['-date_ajout']
        verbose_name = 'Produit'
        verbose_name_plural = 'Produits'

    def __str__(self):
        return self.nom

    def get_image_url(self):
        if self.image and hasattr(self.image, 'url'):
            return self.image.url
        if self.image_url:
            return self.image_url
        return '/static/img/placeholder.jpg'

    @property
    def benefice_unitaire(self):
        return self.prix - self.prix_achat

    @property
    def stock_bas(self):
        return self.stock <= self.seuil_alerte_stock

    @property
    def prix_formate(self):
        return f"{self.prix:,.0f} GNF".replace(",", " ")


class Order(models.Model):
    STATUS_CHOICES = [
        ('nouvelle', 'Nouvelle'),
        ('en_cours', 'En cours'),
        ('terminee', 'Terminée'),
    ]
    PAYMENT_CHOICES = [
        ('orange_money', 'Orange Money'),
        ('mtn_momo', 'MTN MoMo'),
        ('livraison', 'Paiement à la livraison'),
        ('virement', 'Virement bancaire'),
    ]

    numero = models.CharField(max_length=20, unique=True, editable=False)
    prenom_nom = models.CharField(max_length=200, verbose_name="Prénom et Nom")
    telephone = models.CharField(max_length=20, verbose_name="Téléphone / WhatsApp")
    email = models.EmailField(blank=True, null=True)
    adresse = models.TextField(verbose_name="Adresse de livraison")
    mode_paiement = models.CharField(max_length=20, choices=PAYMENT_CHOICES, verbose_name="Mode de paiement")
    notes = models.TextField(blank=True, null=True, verbose_name="Notes / Instructions")
    statut = models.CharField(max_length=20, choices=STATUS_CHOICES, default='nouvelle')
    total = models.DecimalField(max_digits=14, decimal_places=0, default=0)
    date_commande = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date_commande']
        verbose_name = 'Commande'
        verbose_name_plural = 'Commandes'

    def __str__(self):
        return f"Commande {self.numero} - {self.prenom_nom}"

    def save(self, *args, **kwargs):
        if not self.numero:
            self.numero = f"AE-{uuid.uuid4().hex[:8].upper()}"
        super().save(*args, **kwargs)

    @property
    def total_formate(self):
        return f"{self.total:,.0f} GNF".replace(",", " ")


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True)
    nom_produit = models.CharField(max_length=200)
    prix_unitaire = models.DecimalField(max_digits=12, decimal_places=0)
    quantite = models.IntegerField(default=1)

    class Meta:
        verbose_name = "Article commandé"
        verbose_name_plural = "Articles commandés"

    def __str__(self):
        return f"{self.quantite}x {self.nom_produit}"

    @property
    def sous_total(self):
        return self.prix_unitaire * self.quantite

    @property
    def sous_total_formate(self):
        return f"{self.sous_total:,.0f} GNF".replace(",", " ")


class OfflineSale(models.Model):
    CANAL_CHOICES = [
        ('boutique', 'Boutique physique'),
        ('whatsapp', 'WhatsApp'),
        ('telephone', 'Téléphone'),
        ('autre', 'Autre'),
    ]

    produit = models.ForeignKey(
        Product, on_delete=models.SET_NULL, null=True, related_name='ventes_offline'
    )
    nom_produit = models.CharField(max_length=200, verbose_name="Nom du produit")
    quantite = models.IntegerField(default=1)
    prix_vente = models.DecimalField(
        max_digits=12, decimal_places=0, verbose_name="Prix de vente unitaire"
    )
    prix_achat = models.DecimalField(
        max_digits=12, decimal_places=0, default=0, verbose_name="Prix d'achat unitaire"
    )
    canal = models.CharField(
        max_length=20, choices=CANAL_CHOICES, default='boutique', verbose_name="Canal de vente"
    )
    client = models.CharField(max_length=200, blank=True, verbose_name="Nom du client")
    telephone_client = models.CharField(
        max_length=20, blank=True, verbose_name="Téléphone client"
    )
    notes = models.TextField(blank=True, verbose_name="Notes")
    date_vente = models.DateTimeField(auto_now_add=True, verbose_name="Date de vente")

    class Meta:
        ordering = ['-date_vente']
        verbose_name = 'Vente hors site'
        verbose_name_plural = 'Ventes hors site'

    def __str__(self):
        return f"{self.quantite}x {self.nom_produit} ({self.get_canal_display()})"

    def save(self, *args, **kwargs):
        if self.produit and not self.nom_produit:
            self.nom_produit = self.produit.nom
        if self.produit and not self.prix_achat:
            self.prix_achat = self.produit.prix_achat
        super().save(*args, **kwargs)

    @property
    def total(self):
        return self.prix_vente * self.quantite

    @property
    def benefice(self):
        return (self.prix_vente - self.prix_achat) * self.quantite

    @property
    def total_formate(self):
        return f"{self.total:,.0f} GNF".replace(",", " ")

    @property
    def benefice_formate(self):
        return f"{self.benefice:,.0f} GNF".replace(",", " ")


class StockMovement(models.Model):
    TYPE_CHOICES = [
        ('entree', 'Entrée'),
        ('sortie', 'Sortie'),
    ]
    MOTIF_CHOICES = [
        ('achat', 'Achat / Réapprovisionnement'),
        ('vente_en_ligne', 'Vente en ligne'),
        ('vente_hors_site', 'Vente hors site'),
        ('retour', 'Retour client'),
        ('ajustement', 'Ajustement manuel'),
        ('perte', 'Perte / Casse'),
    ]

    produit = models.ForeignKey(
        Product, on_delete=models.CASCADE, related_name='mouvements_stock'
    )
    type_mouvement = models.CharField(max_length=10, choices=TYPE_CHOICES)
    motif = models.CharField(max_length=20, choices=MOTIF_CHOICES, default='ajustement')
    quantite = models.IntegerField()
    stock_avant = models.IntegerField()
    stock_apres = models.IntegerField()
    reference = models.CharField(
        max_length=100, blank=True,
        help_text="Référence commande, vente hors-site, etc."
    )
    notes = models.TextField(blank=True)
    date = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['-date']
        verbose_name = 'Mouvement de stock'
        verbose_name_plural = 'Mouvements de stock'

    def __str__(self):
        return f"{self.get_type_mouvement_display()} {self.quantite}x {self.produit.nom}"


class Expense(models.Model):
    CATEGORY_CHOICES = [
        ('achat_stock', 'Achat de stock'),
        ('transport', 'Transport / Livraison'),
        ('loyer', 'Loyer'),
        ('salaire', 'Salaire'),
        ('marketing', 'Marketing / Publicité'),
        ('autre', 'Autre'),
    ]

    libelle = models.CharField(max_length=200, verbose_name="Libellé")
    montant = models.DecimalField(max_digits=14, decimal_places=0)
    categorie = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='autre')
    notes = models.TextField(blank=True)
    date = models.DateTimeField(default=timezone.now, verbose_name="Date de la dépense")

    class Meta:
        ordering = ['-date']
        verbose_name = 'Dépense'
        verbose_name_plural = 'Dépenses'

    def __str__(self):
        return f"{self.libelle} - {self.montant:,.0f} GNF"

    @property
    def montant_formate(self):
        return f"{self.montant:,.0f} GNF".replace(",", " ")
