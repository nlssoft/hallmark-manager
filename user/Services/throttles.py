from rest_framework.throttling import SimpleRateThrottle


class OTPCooldownThrottling(SimpleRateThrottle):
    scope = "otp_cooldown"

    def get_cache_key(self, request, view):
        email = request.data.get("email", "").strip().lower()

        if not email:
            return self.cache_format % {
                "scope": self.scope,
                "ident": self.get_ident(request),
            }

        return self.cache_format % {
            "scope": self.scope,
            "ident": email,
        }
