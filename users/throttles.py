
from rest_framework.throttling import SimpleRateThrottle

class LoginThrottle(SimpleRateThrottle):
    scope = "login"
    rate = "10/minute"

    def get_cache_key(self, request, view):
        return self.cache_format % {
            "scope": self.scope,
            "ident": self.get_ident(request),
        }

class RegisterThrottle(SimpleRateThrottle):
    scope = "register"
    rate = "10/hour"

    def get_cache_key(self, request, view):
        return self.cache_format % {
            "scope": self.scope,
            "ident": self.get_ident(request),
        }

class EmailThrottle(SimpleRateThrottle):
    scope = "email"
    rate = "3/minute"

    def get_cache_key(self, request, view):
        ident = request.user.pk if request.user.is_authenticated else self.get_ident(request)
        return self.cache_format % {
            "scope": self.scope,
            "ident": ident,
        }