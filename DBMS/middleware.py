import datetime
from django.utils.timezone import now
from django.contrib.auth.models import User
from django.core.cache import cache

class ActiveUserMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        if request.user.is_authenticated:
            # Store current timestamp for user in cache (or DB if preferred)
            cache.set(f'user_last_seen_{request.user.pk}', now(), timeout=300)  # 5 minutes timeout

        return response
    
    
