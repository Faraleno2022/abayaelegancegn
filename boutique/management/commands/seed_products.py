from django.core.management.base import BaseCommand
from boutique.models import Product


class Command(BaseCommand):
    help = 'Ajoute des produits de démonstration au catalogue'

    def handle(self, *args, **options):
        products_data = [
            {
                'nom': 'Robe Élégante Soirée',
                'categorie': 'mode',
                'prix': 850000,
                'description': "Robe longue en tissu satiné, parfaite pour les soirées et événements. Coupe ajustée avec détails brodés à la main. Disponible en plusieurs tailles.",
                'image_url': 'https://images.unsplash.com/photo-1595777457583-95e059d581b8?w=600&h=800&fit=crop',
                'badge': 'Nouveau',
                'note': 5,
                'stock': 15,
            },
            {
                'nom': 'Costume Homme Premium',
                'categorie': 'mode',
                'prix': 1200000,
                'description': "Costume trois pièces en laine fine. Coupe moderne et élégante, idéal pour les occasions professionnelles et cérémonies. Finitions soignées.",
                'image_url': 'https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=600&h=800&fit=crop',
                'badge': 'Premium',
                'note': 5,
                'stock': 8,
            },
            {
                'nom': 'Sac à Main Cuir',
                'categorie': 'accessoires',
                'prix': 450000,
                'description': "Sac à main en cuir véritable avec finitions dorées. Design intemporel et pratique avec multiples compartiments. Bandoulière ajustable incluse.",
                'image_url': 'https://images.unsplash.com/photo-1584917865442-de89df76afd3?w=600&h=800&fit=crop',
                'badge': 'Bestseller',
                'note': 5,
                'stock': 20,
            },
            {
                'nom': 'Montre Classique Or',
                'categorie': 'accessoires',
                'prix': 680000,
                'description': "Montre classique avec bracelet en cuir et cadran doré. Mouvement à quartz de haute précision. Résistante à l'eau jusqu'à 30 mètres.",
                'image_url': 'https://images.unsplash.com/photo-1524592094714-0f0654e20314?w=600&h=800&fit=crop',
                'badge': 'Exclusif',
                'note': 4,
                'stock': 12,
            },
            {
                'nom': 'Ensemble Wax Africain',
                'categorie': 'mode',
                'prix': 350000,
                'description': "Ensemble deux pièces en tissu wax authentique. Motifs traditionnels revisités avec une touche moderne. Tissu 100% coton de qualité supérieure.",
                'image_url': 'https://images.unsplash.com/photo-1590735213920-68192a487bc2?w=600&h=800&fit=crop',
                'badge': 'Nouveau',
                'note': 5,
                'stock': 25,
            },
            {
                'nom': 'Collier Perles Dorées',
                'categorie': 'accessoires',
                'prix': 180000,
                'description': "Collier de perles dorées artisanal. Design élégant et raffiné, parfait pour sublimer toute tenue. Fermoir en plaqué or.",
                'image_url': 'https://images.unsplash.com/photo-1599643478518-a784e5dc4c8f?w=600&h=800&fit=crop',
                'badge': '',
                'note': 4,
                'stock': 30,
            },
            {
                'nom': 'Coussin Décoratif Luxe',
                'categorie': 'maison',
                'prix': 120000,
                'description': "Coussin décoratif en velours avec broderies dorées. Dimensions 45x45cm. Housse lavable avec fermeture invisible. Garnissage hypoallergénique.",
                'image_url': 'https://images.unsplash.com/photo-1584100936595-c0654b55a2e2?w=600&h=800&fit=crop',
                'badge': '',
                'note': 4,
                'stock': 40,
            },
            {
                'nom': 'Vase Artisanal Doré',
                'categorie': 'maison',
                'prix': 250000,
                'description': "Vase artisanal en céramique avec finition dorée. Pièce unique fabriquée à la main. Hauteur 35cm. Parfait comme centre de table ou décoration.",
                'image_url': 'https://images.unsplash.com/photo-1578500494198-246f612d3b3d?w=600&h=800&fit=crop',
                'badge': 'Exclusif',
                'note': 5,
                'stock': 10,
            },
            {
                'nom': 'Chemise Lin Homme',
                'categorie': 'mode',
                'prix': 280000,
                'description': "Chemise en lin naturel, coupe décontractée et élégante. Tissu respirant idéal pour le climat tropical. Col mao avec boutons en nacre.",
                'image_url': 'https://images.unsplash.com/photo-1602810318383-e386cc2a3ccf?w=600&h=800&fit=crop',
                'badge': '',
                'note': 4,
                'stock': 18,
            },
            {
                'nom': 'Bougie Parfumée Premium',
                'categorie': 'maison',
                'prix': 95000,
                'description': "Bougie parfumée artisanale à la cire de soja. Parfum boisé et vanillé. Durée de combustion environ 50 heures. Contenant réutilisable en verre soufflé.",
                'image_url': 'https://images.unsplash.com/photo-1602528495711-40a4e7a5a3de?w=600&h=800&fit=crop',
                'badge': 'Bestseller',
                'note': 5,
                'stock': 35,
            },
            {
                'nom': 'Lunettes de Soleil Fashion',
                'categorie': 'accessoires',
                'prix': 220000,
                'description': "Lunettes de soleil unisexes avec monture dorée et verres polarisés. Protection UV400. Design tendance et intemporel. Étui rigide inclus.",
                'image_url': 'https://images.unsplash.com/photo-1572635196237-14b3f281503f?w=600&h=800&fit=crop',
                'badge': '',
                'note': 4,
                'stock': 22,
            },
            {
                'nom': 'Plateau Service Doré',
                'categorie': 'maison',
                'prix': 175000,
                'description': "Plateau de service en métal avec finition dorée martelée. Dimensions 40x25cm. Parfait pour servir le thé ou comme pièce décorative.",
                'image_url': 'https://images.unsplash.com/photo-1584589167171-541ce45f1eea?w=600&h=800&fit=crop',
                'badge': 'Premium',
                'note': 5,
                'stock': 15,
            },
        ]

        created_count = 0
        for data in products_data:
            product, created = Product.objects.get_or_create(
                nom=data['nom'],
                defaults=data
            )
            if created:
                created_count += 1
                self.stdout.write(self.style.SUCCESS(f'  ✓ Produit créé : {product.nom}'))
            else:
                self.stdout.write(self.style.WARNING(f'  → Produit existant : {product.nom}'))

        self.stdout.write(self.style.SUCCESS(f'\n{created_count} produit(s) créé(s) sur {len(products_data)} au total.'))
