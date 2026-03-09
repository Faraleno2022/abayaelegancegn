from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.urls import reverse
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Sum, Count
from django.db import transaction
from django.views.decorators.http import require_POST
from .models import Product, Order, OrderItem
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

    context = {
        'total_orders': total_orders,
        'pending_orders': pending_orders,
        'in_progress_orders': in_progress_orders,
        'completed_orders': completed_orders,
        'total_revenue': total_revenue,
        'total_revenue_formate': f"{total_revenue:,.0f} GNF".replace(",", " "),
        'total_products': total_products,
        'recent_orders': recent_orders,
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
    order.statut = 'terminee'
    order.save(update_fields=['statut'])
    messages.success(request, f'Commande {order.numero} marquée comme traitée.')
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
