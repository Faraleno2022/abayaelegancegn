from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.urls import reverse
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Sum, Count, F
from django.db import transaction
from django.views.decorators.http import require_POST
from django.utils import timezone
from datetime import timedelta
from .models import Product, Order, OrderItem, OfflineSale, StockMovement, Expense
import json


def home(request):
    products = Product.objects.filter(actif=True)
    categorie = request.GET.get('categorie', 'tout')
    search = request.GET.get('q', '')

    if search:
        products = products.filter(
            Q(nom__icontains=search) |
            Q(categorie__icontains=search) |
            Q(description__icontains=search)
        )

    if categorie and categorie != 'tout':
        products = products.filter(categorie=categorie)

    context = {
        'products': products,
        'categorie_active': categorie,
        'search_query': search,
        'total_products': Product.objects.filter(actif=True).count(),
        'categories': [
            ('tout', 'Tout'),
            ('mode', 'Mode'),
            ('accessoires', 'Accessoires'),
            ('maison', 'Maison'),
        ],
    }
    return render(request, 'boutique/home.html', context)


def product_detail(request, pk):
    product = get_object_or_404(Product, pk=pk, actif=True)

    if request.GET.get('fbclid'):
        return redirect('commande_directe', pk=product.pk)

    related = Product.objects.filter(categorie=product.categorie, actif=True).exclude(pk=pk)[:4]
    context = {
        'product': product,
        'related_products': related,
    }
    return render(request, 'boutique/product_detail.html', context)


def about(request):
    return render(request, 'boutique/about.html')


def cart_view(request):
    cart = request.session.get('cart', {})
    cart_items = []
    total = 0

    for product_id, qty in cart.items():
        try:
            product = Product.objects.get(pk=int(product_id), actif=True)
            sous_total = product.prix * qty
            total += sous_total
            cart_items.append({
                'product': product,
                'quantity': qty,
                'sous_total': sous_total,
                'sous_total_formate': f"{sous_total:,.0f} GNF".replace(",", " "),
            })
        except Product.DoesNotExist:
            continue

    context = {
        'cart_items': cart_items,
        'total': total,
        'total_formate': f"{total:,.0f} GNF".replace(",", " "),
        'payment_methods': Order.PAYMENT_CHOICES,
    }
    return render(request, 'boutique/cart.html', context)


def add_to_cart(request, pk):
    product = get_object_or_404(Product, pk=pk, actif=True)
    cart = request.session.get('cart', {})
    product_id = str(pk)
    qty = int(request.POST.get('quantity', 1)) if request.method == 'POST' else 1

    if product_id in cart:
        cart[product_id] += qty
    else:
        cart[product_id] = qty

    request.session['cart'] = cart
    messages.success(request, f'"{product.nom}" ajouté au panier !')

    next_url = request.POST.get('next', request.META.get('HTTP_REFERER', '/'))
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'success': True,
            'cart_count': sum(cart.values()),
            'message': f'"{product.nom}" ajouté au panier !'
        })
    return redirect(next_url)


def update_cart(request, pk):
    cart = request.session.get('cart', {})
    product_id = str(pk)
    action = request.POST.get('action', '')

    if action == 'increase':
        cart[product_id] = cart.get(product_id, 0) + 1
    elif action == 'decrease':
        if cart.get(product_id, 0) > 1:
            cart[product_id] -= 1
        else:
            cart.pop(product_id, None)
    elif action == 'remove':
        cart.pop(product_id, None)

    request.session['cart'] = cart
    return redirect('cart')


def checkout(request):
    if request.method != 'POST':
        return redirect('cart')

    cart = request.session.get('cart', {})
    if not cart:
        messages.error(request, 'Votre panier est vide.')
        return redirect('cart')

    prenom_nom = request.POST.get('prenom_nom', '').strip()
    telephone = request.POST.get('telephone', '').strip()
    email = request.POST.get('email', '').strip()
    adresse = request.POST.get('adresse', '').strip()
    mode_paiement = request.POST.get('mode_paiement', '')
    notes = request.POST.get('notes', '').strip()

    if not all([prenom_nom, telephone, adresse, mode_paiement]):
        messages.error(request, 'Veuillez remplir tous les champs obligatoires.')
        return redirect('cart')

    order = Order.objects.create(
        prenom_nom=prenom_nom,
        telephone=telephone,
        email=email or None,
        adresse=adresse,
        mode_paiement=mode_paiement,
        notes=notes or None,
    )

    total = 0
    for product_id, qty in cart.items():
        try:
            product = Product.objects.get(pk=int(product_id))
            sous_total = product.prix * qty
            total += sous_total
            OrderItem.objects.create(
                order=order,
                product=product,
                nom_produit=product.nom,
                prix_unitaire=product.prix,
                quantite=qty,
            )
        except Product.DoesNotExist:
            continue

    order.total = total
    order.save()

    request.session['cart'] = {}
    request.session['last_order_id'] = order.id

    return redirect(f"{reverse('order_confirmation', kwargs={'numero': order.numero})}?redirect_home=1")


def order_confirmation(request, numero):
    order = get_object_or_404(Order, numero=numero)
    context = {
        'order': order,
        'redirect_home': request.GET.get('redirect_home') == '1',
    }
    return render(request, 'boutique/order_confirmation.html', context)


def cart_count(request):
    cart = request.session.get('cart', {})
    return JsonResponse({'count': sum(cart.values())})


# ============ COMMANDE EN LIGNE (lien partageable) ============

def commander_en_ligne(request):
    products = Product.objects.filter(actif=True)
    categorie = request.GET.get('categorie', 'tout')

    if categorie and categorie != 'tout':
        products = products.filter(categorie=categorie)

    context = {
        'products': products,
        'categorie_active': categorie,
        'categories': [
            ('tout', 'Tout'),
            ('mode', 'Mode'),
            ('accessoires', 'Accessoires'),
            ('maison', 'Maison'),
        ],
        'payment_methods': Order.PAYMENT_CHOICES,
    }
    return render(request, 'boutique/commander_en_ligne.html', context)


def commander_en_ligne_submit(request):
    if request.method != 'POST':
        return redirect('commander_en_ligne')

    prenom_nom = request.POST.get('prenom_nom', '').strip()
    telephone = request.POST.get('telephone', '').strip()
    email = request.POST.get('email', '').strip()
    adresse = request.POST.get('adresse', '').strip()
    mode_paiement = request.POST.get('mode_paiement', '')
    notes = request.POST.get('notes', '').strip()
    produits_json = request.POST.get('produits', '{}')

    if not all([prenom_nom, telephone, adresse, mode_paiement]):
        messages.error(request, 'Veuillez remplir tous les champs obligatoires.')
        return redirect('commander_en_ligne')

    try:
        produits_selectionnes = json.loads(produits_json)
    except json.JSONDecodeError:
        produits_selectionnes = {}

    if not produits_selectionnes:
        messages.error(request, 'Veuillez sélectionner au moins un produit.')
        return redirect('commander_en_ligne')

    order = Order.objects.create(
        prenom_nom=prenom_nom,
        telephone=telephone,
        email=email or None,
        adresse=adresse,
        mode_paiement=mode_paiement,
        notes=notes or None,
    )

    total = 0
    for product_id, qty in produits_selectionnes.items():
        qty = int(qty)
        if qty <= 0:
            continue
        try:
            product = Product.objects.get(pk=int(product_id), actif=True)
            sous_total = product.prix * qty
            total += sous_total
            OrderItem.objects.create(
                order=order,
                product=product,
                nom_produit=product.nom,
                prix_unitaire=product.prix,
                quantite=qty,
            )
        except Product.DoesNotExist:
            continue

    if total == 0:
        order.delete()
        messages.error(request, 'Aucun produit valide sélectionné.')
        return redirect('commander_en_ligne')

    order.total = total
    order.save()

    return redirect(f"{reverse('order_confirmation', kwargs={'numero': order.numero})}?redirect_home=1")


def commande_video(request):
    context = {
        'payment_methods': Order.PAYMENT_CHOICES,
    }
    return render(request, 'boutique/commande_video.html', context)


def commande_video_submit(request):
    if request.method != 'POST':
        return redirect('commande_video')

    prenom_nom = request.POST.get('prenom_nom', '').strip()
    telephone = request.POST.get('telephone', '').strip()
    email = request.POST.get('email', '').strip()
    adresse = request.POST.get('adresse', '').strip()
    mode_paiement = request.POST.get('mode_paiement', '')
    notes = request.POST.get('notes', '').strip()
    produit_video = request.POST.get('produit_video', '').strip()

    if not all([prenom_nom, telephone, adresse, mode_paiement, produit_video]):
        messages.error(request, 'Veuillez remplir tous les champs obligatoires.')
        return redirect('commande_video')

    notes_completes = f"Produit vu dans la vidéo : {produit_video}"
    if notes:
        notes_completes = f"{notes_completes}\n\nNotes client : {notes}"

    order = Order.objects.create(
        prenom_nom=prenom_nom,
        telephone=telephone,
        email=email or None,
        adresse=adresse,
        mode_paiement=mode_paiement,
        notes=notes_completes,
        total=0,
    )

    return redirect(f"{reverse('order_confirmation', kwargs={'numero': order.numero})}?redirect_home=1")


# ============ COMMANDE DIRECTE PAR PRODUIT (lien partageable) ============

def commande_directe(request, pk):
    product = get_object_or_404(Product, pk=pk, actif=True)
    context = {
        'product': product,
        'payment_methods': Order.PAYMENT_CHOICES,
    }
    return render(request, 'boutique/commande_directe.html', context)


def commande_directe_submit(request, pk):
    if request.method != 'POST':
        return redirect('commande_directe', pk=pk)

    product = get_object_or_404(Product, pk=pk, actif=True)

    prenom_nom = request.POST.get('prenom_nom', '').strip()
    telephone = request.POST.get('telephone', '').strip()
    email = request.POST.get('email', '').strip()
    adresse = request.POST.get('adresse', '').strip()
    mode_paiement = request.POST.get('mode_paiement', '')
    notes = request.POST.get('notes', '').strip()
    quantite = int(request.POST.get('quantite', 1))

    if not all([prenom_nom, telephone, adresse, mode_paiement]):
        messages.error(request, 'Veuillez remplir tous les champs obligatoires.')
        return redirect('commande_directe', pk=pk)

    if quantite < 1:
        quantite = 1

    sous_total = product.prix * quantite

    order = Order.objects.create(
        prenom_nom=prenom_nom,
        telephone=telephone,
        email=email or None,
        adresse=adresse,
        mode_paiement=mode_paiement,
        notes=notes or None,
        total=sous_total,
    )

    OrderItem.objects.create(
        order=order,
        product=product,
        nom_produit=product.nom,
        prix_unitaire=product.prix,
        quantite=quantite,
    )

    return redirect(f"{reverse('order_confirmation', kwargs={'numero': order.numero})}?redirect_home=1")


# ============ ADMIN VIEWS ============

def admin_login(request):
    if request.user.is_authenticated and request.user.is_staff:
        return redirect('admin_dashboard')

    if request.method == 'POST':
        username = request.POST.get('username', '')
        password = request.POST.get('password', '')
        user = authenticate(request, username=username, password=password)
        if user is not None and user.is_staff:
            login(request, user)
            return redirect('admin_dashboard')
        else:
            messages.error(request, 'Identifiants incorrects ou accès non autorisé.')

    return render(request, 'boutique/admin/login.html')


@login_required
def admin_dashboard(request):
    if not request.user.is_staff:
        return redirect('home')

    total_orders = Order.objects.count()
    pending_orders = Order.objects.filter(statut='nouvelle').count()
    in_progress_orders = Order.objects.filter(statut='en_cours').count()
    completed_orders = Order.objects.filter(statut='terminee').count()
    total_revenue = Order.objects.filter(statut='terminee').aggregate(Sum('total'))['total__sum'] or 0
    total_products = Product.objects.filter(actif=True).count()
    recent_orders = Order.objects.all()[:10]

    # Alertes stock
    produits_alerte = Product.objects.filter(
        actif=True, stock__lte=F('seuil_alerte_stock')
    ).exclude(stock=0)
    produits_rupture = Product.objects.filter(actif=True, stock=0)

    context = {
        'total_orders': total_orders,
        'pending_orders': pending_orders,
        'in_progress_orders': in_progress_orders,
        'completed_orders': completed_orders,
        'total_revenue': total_revenue,
        'total_revenue_formate': f"{total_revenue:,.0f} GNF".replace(",", " "),
        'total_products': total_products,
        'recent_orders': recent_orders,
        'produits_alerte': produits_alerte,
        'nb_produits_alerte': produits_alerte.count(),
        'produits_rupture': produits_rupture,
        'nb_produits_rupture': produits_rupture.count(),
    }
    return render(request, 'boutique/admin/dashboard.html', context)


@login_required
def admin_orders(request):
    if not request.user.is_staff:
        return redirect('home')

    statut_filter = request.GET.get('statut', '')
    orders = Order.objects.all()

    if statut_filter:
        orders = orders.filter(statut=statut_filter)
    else:
        orders = orders.exclude(statut='terminee')

    context = {
        'orders': orders,
        'statut_filter': statut_filter,
        'statuts': Order.STATUS_CHOICES,
    }
    return render(request, 'boutique/admin/orders.html', context)


@login_required
def admin_order_detail(request, pk):
    if not request.user.is_staff:
        return redirect('home')

    order = get_object_or_404(Order, pk=pk)
    context = {'order': order}
    return render(request, 'boutique/admin/order_detail.html', context)


@login_required
@require_POST
def admin_update_status(request, pk):
    if not request.user.is_staff:
        return redirect('home')

    order = get_object_or_404(Order, pk=pk)
    new_status = request.POST.get('statut', '')
    if new_status in dict(Order.STATUS_CHOICES):
        order.statut = new_status
        order.save()
        messages.success(request, f'Statut de la commande {order.numero} mis à jour.')
    return redirect('admin_order_detail', pk=pk)


@login_required
@require_POST
def admin_mark_order_completed(request, pk):
    if not request.user.is_staff:
        return redirect('home')

    order = get_object_or_404(Order, pk=pk)
    if order.statut == 'terminee':
        messages.info(request, f'Commande {order.numero} est déjà terminée.')
        return redirect('admin_orders')

    with transaction.atomic():
        order.statut = 'terminee'
        order.save(update_fields=['statut'])

        for item in order.items.all():
            if item.product:
                stock_avant = item.product.stock
                item.product.stock = max(0, item.product.stock - item.quantite)
                item.product.save(update_fields=['stock'])

                StockMovement.objects.create(
                    produit=item.product,
                    type_mouvement='sortie',
                    motif='vente_en_ligne',
                    quantite=item.quantite,
                    stock_avant=stock_avant,
                    stock_apres=item.product.stock,
                    reference=f'Commande {order.numero}',
                )

    messages.success(request, f'Commande {order.numero} marquée comme traitée. Stock mis à jour.')
    return redirect('admin_orders')


# ============ PRODUCT MANAGEMENT ============

@login_required
def admin_products(request):
    if not request.user.is_staff:
        return redirect('home')

    search = request.GET.get('q', '')
    categorie = request.GET.get('categorie', '')
    products = Product.objects.all()

    if search:
        products = products.filter(
            Q(nom__icontains=search) | Q(description__icontains=search)
        )
    if categorie:
        products = products.filter(categorie=categorie)

    context = {
        'products': products,
        'search_query': search,
        'categorie_filter': categorie,
        'categories': Product.CATEGORY_CHOICES,
        'total': products.count(),
    }
    return render(request, 'boutique/admin/products.html', context)


@login_required
def admin_product_add(request):
    if not request.user.is_staff:
        return redirect('home')

    if request.method == 'POST':
        nom = request.POST.get('nom', '').strip()
        categorie = request.POST.get('categorie', '')
        prix = request.POST.get('prix', '0')
        description = request.POST.get('description', '').strip()
        image_url = request.POST.get('image_url', '').strip()
        badge = request.POST.get('badge', '')
        note = request.POST.get('note', '5')
        stock = request.POST.get('stock', '0')
        actif = request.POST.get('actif') == 'on'

        if not all([nom, categorie, prix, description]):
            messages.error(request, 'Veuillez remplir tous les champs obligatoires.')
            return render(request, 'boutique/admin/product_form.html', {
                'mode': 'add',
                'categories': Product.CATEGORY_CHOICES,
                'badges': Product.BADGE_CHOICES,
                'form_data': request.POST,
            })

        product = Product(
            nom=nom,
            categorie=categorie,
            prix=int(prix),
            description=description,
            image_url=image_url or None,
            badge=badge,
            note=int(note),
            stock=int(stock),
            actif=actif,
        )

        if 'image' in request.FILES:
            product.image = request.FILES['image']

        product.save()
        messages.success(request, f'Produit "{product.nom}" ajouté avec succès !')
        return redirect('admin_products')

    context = {
        'mode': 'add',
        'categories': Product.CATEGORY_CHOICES,
        'badges': Product.BADGE_CHOICES,
    }
    return render(request, 'boutique/admin/product_form.html', context)


@login_required
def admin_product_edit(request, pk):
    if not request.user.is_staff:
        return redirect('home')

    product = get_object_or_404(Product, pk=pk)

    if request.method == 'POST':
        product.nom = request.POST.get('nom', '').strip()
        product.categorie = request.POST.get('categorie', '')
        product.prix = int(request.POST.get('prix', '0'))
        product.description = request.POST.get('description', '').strip()
        product.badge = request.POST.get('badge', '')
        product.note = int(request.POST.get('note', '5'))
        product.stock = int(request.POST.get('stock', '0'))
        product.actif = request.POST.get('actif') == 'on'

        image_url = request.POST.get('image_url', '').strip()
        if image_url:
            product.image_url = image_url

        if 'image' in request.FILES:
            product.image = request.FILES['image']

        if not all([product.nom, product.categorie, product.prix, product.description]):
            messages.error(request, 'Veuillez remplir tous les champs obligatoires.')
        else:
            product.save()
            messages.success(request, f'Produit "{product.nom}" mis à jour avec succès !')
            return redirect('admin_products')

    context = {
        'mode': 'edit',
        'product': product,
        'categories': Product.CATEGORY_CHOICES,
        'badges': Product.BADGE_CHOICES,
    }
    return render(request, 'boutique/admin/product_form.html', context)


@login_required
@require_POST
def admin_product_delete(request, pk):
    if not request.user.is_staff:
        return redirect('home')

    product = get_object_or_404(Product, pk=pk)
    nom = product.nom

    try:
        with transaction.atomic():
            if product.image:
                product.image.delete(save=False)
            product.delete()
        messages.success(request, f'Produit "{nom}" supprimé définitivement.')
    except Exception:
        messages.error(request, f'Impossible de supprimer le produit "{nom}" pour le moment.')

    return redirect('admin_products')


@login_required
def admin_logout(request):
    logout(request)
    messages.success(request, 'Déconnexion réussie.')
    return redirect('home')


# ============ COMPTABILITÉ ============

@login_required
def admin_comptabilite(request):
    if not request.user.is_staff:
        return redirect('home')

    # Période par défaut : ce mois
    periode = request.GET.get('periode', 'mois')
    now = timezone.now()

    if periode == 'jour':
        date_debut = now.replace(hour=0, minute=0, second=0, microsecond=0)
        label_periode = "Aujourd'hui"
    elif periode == 'semaine':
        date_debut = (now - timedelta(days=now.weekday())).replace(hour=0, minute=0, second=0, microsecond=0)
        label_periode = "Cette semaine"
    elif periode == 'mois':
        date_debut = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        label_periode = "Ce mois"
    elif periode == 'annee':
        date_debut = now.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
        label_periode = "Cette année"
    else:
        date_debut = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        label_periode = "Ce mois"

    # Revenus en ligne (commandes terminées)
    commandes_terminees = Order.objects.filter(statut='terminee', date_commande__gte=date_debut)
    ca_en_ligne = commandes_terminees.aggregate(total=Sum('total'))['total'] or 0
    nb_commandes = commandes_terminees.count()

    # Coût d'achat des ventes en ligne
    cout_achat_en_ligne = 0
    for cmd in commandes_terminees:
        for item in cmd.items.all():
            if item.product:
                cout_achat_en_ligne += item.product.prix_achat * item.quantite
            else:
                cout_achat_en_ligne += 0

    # Ventes hors site
    ventes_offline = OfflineSale.objects.filter(date_vente__gte=date_debut)
    ca_hors_site = ventes_offline.aggregate(total=Sum(F('prix_vente') * F('quantite')))['total'] or 0
    benefice_hors_site = 0
    for v in ventes_offline:
        benefice_hors_site += v.benefice
    nb_ventes_offline = ventes_offline.count()

    # Dépenses
    depenses = Expense.objects.filter(date__gte=date_debut)
    total_depenses = depenses.aggregate(total=Sum('montant'))['total'] or 0

    # Calculs
    ca_total = ca_en_ligne + ca_hors_site
    benefice_en_ligne = ca_en_ligne - cout_achat_en_ligne
    benefice_brut = benefice_en_ligne + benefice_hors_site
    benefice_net = benefice_brut - total_depenses

    # Dépenses par catégorie
    depenses_par_categorie = depenses.values('categorie').annotate(
        total=Sum('montant')
    ).order_by('-total')

    # Dernières dépenses
    dernieres_depenses = depenses[:10]

    # Valeur du stock
    produits = Product.objects.filter(actif=True)
    valeur_stock_achat = sum(p.prix_achat * p.stock for p in produits)
    valeur_stock_vente = sum(p.prix * p.stock for p in produits)

    def fmt(val):
        return f"{val:,.0f} GNF".replace(",", " ")

    context = {
        'periode': periode,
        'label_periode': label_periode,
        'ca_en_ligne': ca_en_ligne,
        'ca_en_ligne_f': fmt(ca_en_ligne),
        'ca_hors_site': ca_hors_site,
        'ca_hors_site_f': fmt(ca_hors_site),
        'ca_total': ca_total,
        'ca_total_f': fmt(ca_total),
        'benefice_en_ligne': benefice_en_ligne,
        'benefice_en_ligne_f': fmt(benefice_en_ligne),
        'benefice_hors_site': benefice_hors_site,
        'benefice_hors_site_f': fmt(benefice_hors_site),
        'benefice_brut': benefice_brut,
        'benefice_brut_f': fmt(benefice_brut),
        'total_depenses': total_depenses,
        'total_depenses_f': fmt(total_depenses),
        'benefice_net': benefice_net,
        'benefice_net_f': fmt(benefice_net),
        'nb_commandes': nb_commandes,
        'nb_ventes_offline': nb_ventes_offline,
        'depenses_par_categorie': depenses_par_categorie,
        'dernieres_depenses': dernieres_depenses,
        'valeur_stock_achat': valeur_stock_achat,
        'valeur_stock_achat_f': fmt(valeur_stock_achat),
        'valeur_stock_vente': valeur_stock_vente,
        'valeur_stock_vente_f': fmt(valeur_stock_vente),
        'expense_categories': Expense.CATEGORY_CHOICES,
    }
    return render(request, 'boutique/admin/comptabilite.html', context)


# ============ GESTION DE STOCK ============

@login_required
def admin_stock(request):
    if not request.user.is_staff:
        return redirect('home')

    products = Product.objects.filter(actif=True).order_by('stock')
    filtre = request.GET.get('filtre', '')

    if filtre == 'alerte':
        products = [p for p in products if p.stock_bas]
    elif filtre == 'rupture':
        products = Product.objects.filter(actif=True, stock=0).order_by('nom')

    produits_alerte = Product.objects.filter(
        actif=True, stock__lte=F('seuil_alerte_stock')
    ).count()
    produits_rupture = Product.objects.filter(actif=True, stock=0).count()

    mouvements_recents = StockMovement.objects.all()[:20]

    context = {
        'products': products,
        'filtre': filtre,
        'produits_alerte': produits_alerte,
        'produits_rupture': produits_rupture,
        'mouvements_recents': mouvements_recents,
        'total_produits': Product.objects.filter(actif=True).count(),
    }
    return render(request, 'boutique/admin/stock.html', context)


@login_required
@require_POST
def admin_stock_entry(request):
    """Entrée de stock (réapprovisionnement)"""
    if not request.user.is_staff:
        return redirect('home')

    product_id = request.POST.get('produit')
    quantite = int(request.POST.get('quantite', 0))
    motif = request.POST.get('motif', 'achat')
    notes = request.POST.get('notes', '').strip()

    if quantite <= 0:
        messages.error(request, 'La quantité doit être supérieure à 0.')
        return redirect('admin_stock')

    product = get_object_or_404(Product, pk=product_id)

    with transaction.atomic():
        stock_avant = product.stock
        product.stock += quantite
        product.save(update_fields=['stock'])

        StockMovement.objects.create(
            produit=product,
            type_mouvement='entree',
            motif=motif,
            quantite=quantite,
            stock_avant=stock_avant,
            stock_apres=product.stock,
            notes=notes,
        )

    messages.success(request, f'+{quantite} unité(s) ajoutée(s) au stock de « {product.nom} » (Stock: {product.stock})')
    return redirect('admin_stock')


@login_required
@require_POST
def admin_stock_exit(request):
    """Sortie de stock manuelle (perte, ajustement, etc.)"""
    if not request.user.is_staff:
        return redirect('home')

    product_id = request.POST.get('produit')
    quantite = int(request.POST.get('quantite', 0))
    motif = request.POST.get('motif', 'ajustement')
    notes = request.POST.get('notes', '').strip()

    if quantite <= 0:
        messages.error(request, 'La quantité doit être supérieure à 0.')
        return redirect('admin_stock')

    product = get_object_or_404(Product, pk=product_id)

    if quantite > product.stock:
        messages.error(request, f'Stock insuffisant. Stock actuel : {product.stock}')
        return redirect('admin_stock')

    with transaction.atomic():
        stock_avant = product.stock
        product.stock -= quantite
        product.save(update_fields=['stock'])

        StockMovement.objects.create(
            produit=product,
            type_mouvement='sortie',
            motif=motif,
            quantite=quantite,
            stock_avant=stock_avant,
            stock_apres=product.stock,
            notes=notes,
        )

    messages.success(request, f'-{quantite} unité(s) retirée(s) du stock de « {product.nom} » (Stock: {product.stock})')
    return redirect('admin_stock')


# ============ VENTES HORS SITE ============

@login_required
def admin_offline_sales(request):
    if not request.user.is_staff:
        return redirect('home')

    ventes = OfflineSale.objects.all()
    canal_filter = request.GET.get('canal', '')
    if canal_filter:
        ventes = ventes.filter(canal=canal_filter)

    total_ventes = ventes.aggregate(
        total=Sum(F('prix_vente') * F('quantite'))
    )['total'] or 0
    total_benefice = sum(v.benefice for v in ventes)

    def fmt(val):
        return f"{val:,.0f} GNF".replace(",", " ")

    context = {
        'ventes': ventes[:50],
        'canal_filter': canal_filter,
        'canaux': OfflineSale.CANAL_CHOICES,
        'total_ventes': total_ventes,
        'total_ventes_f': fmt(total_ventes),
        'total_benefice': total_benefice,
        'total_benefice_f': fmt(total_benefice),
        'nb_ventes': ventes.count(),
        'products': Product.objects.filter(actif=True),
    }
    return render(request, 'boutique/admin/offline_sales.html', context)


@login_required
@require_POST
def admin_offline_sale_add(request):
    if not request.user.is_staff:
        return redirect('home')

    product_id = request.POST.get('produit')
    quantite = int(request.POST.get('quantite', 1))
    prix_vente = int(request.POST.get('prix_vente', 0))
    canal = request.POST.get('canal', 'boutique')
    client = request.POST.get('client', '').strip()
    telephone_client = request.POST.get('telephone_client', '').strip()
    notes = request.POST.get('notes', '').strip()

    if quantite <= 0 or prix_vente <= 0:
        messages.error(request, 'Quantité et prix doivent être supérieurs à 0.')
        return redirect('admin_offline_sales')

    product = get_object_or_404(Product, pk=product_id)

    with transaction.atomic():
        sale = OfflineSale.objects.create(
            produit=product,
            nom_produit=product.nom,
            quantite=quantite,
            prix_vente=prix_vente,
            prix_achat=product.prix_achat,
            canal=canal,
            client=client,
            telephone_client=telephone_client,
            notes=notes,
        )

        # Déduire le stock
        stock_avant = product.stock
        product.stock = max(0, product.stock - quantite)
        product.save(update_fields=['stock'])

        StockMovement.objects.create(
            produit=product,
            type_mouvement='sortie',
            motif='vente_hors_site',
            quantite=quantite,
            stock_avant=stock_avant,
            stock_apres=product.stock,
            reference=f'Vente hors-site #{sale.pk}',
        )

    messages.success(request, f'Vente de {quantite}x « {product.nom} » enregistrée. Stock mis à jour.')
    return redirect('admin_offline_sales')


# ============ DÉPENSES ============

@login_required
@require_POST
def admin_expense_add(request):
    if not request.user.is_staff:
        return redirect('home')

    libelle = request.POST.get('libelle', '').strip()
    montant = int(request.POST.get('montant', 0))
    categorie = request.POST.get('categorie', 'autre')
    notes = request.POST.get('notes', '').strip()

    if not libelle or montant <= 0:
        messages.error(request, 'Libellé et montant sont obligatoires.')
        return redirect('admin_comptabilite')

    Expense.objects.create(
        libelle=libelle,
        montant=montant,
        categorie=categorie,
        notes=notes,
    )
    messages.success(request, f'Dépense « {libelle} » enregistrée.')
    return redirect('admin_comptabilite')


@login_required
@require_POST
def admin_expense_delete(request, pk):
    if not request.user.is_staff:
        return redirect('home')

    expense = get_object_or_404(Expense, pk=pk)
    expense.delete()
    messages.success(request, 'Dépense supprimée.')
    return redirect('admin_comptabilite')
