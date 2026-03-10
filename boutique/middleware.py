from django.conf import settings
from django.http import HttpResponsePermanentRedirect


class CanonicalHostMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        canonical_domain = getattr(settings, 'CANONICAL_DOMAIN', '')
        canonical_scheme = getattr(settings, 'CANONICAL_SCHEME', 'https')
        host = request.get_host().split(':')[0]

        if canonical_domain and host not in {'localhost', '127.0.0.1'} and host != canonical_domain:
            canonical_url = f"{canonical_scheme}://{canonical_domain}{request.get_full_path()}"
            return HttpResponsePermanentRedirect(canonical_url)

        return self.get_response(request)
