from django.db import models
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
