from django.conf import settings


def cart_context(request):
    cart = request.session.get('cart', {})
    return {
        'cart_count': sum(cart.values()) if cart else 0,
    }


def seo_context(request):
    canonical_scheme = getattr(settings, 'CANONICAL_SCHEME', 'https')
    canonical_domain = getattr(settings, 'CANONICAL_DOMAIN', request.get_host())
    canonical_base_url = f"{canonical_scheme}://{canonical_domain}"

    return {
        'canonical_base_url': canonical_base_url,
        'canonical_current_url': f"{canonical_base_url}{request.get_full_path()}",
    }
