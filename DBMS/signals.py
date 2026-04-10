from django.dispatch import receiver 
from django.utils.timezone import now
from django.contrib.auth.models import User
from .models import UserActivity
from django.contrib.auth.signals import user_logged_in, user_logged_out
from django.db.models.signals import post_save, post_delete
from .utils.audit_logger import log_audit
import sys


def is_running_migrations():
    """Check if Django is currently running migrations."""
    return 'migrate' in sys.argv or 'makemigrations' in sys.argv


def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        return x_forwarded_for.split(',')[0]
    return request.META.get('REMOTE_ADDR')


def get_model_name(instance):
    return instance.__class__.__name__


def create_activity_if_not_duplicate(user, action, method, path, ip):
    """Avoid duplicate consecutive user activities."""
    if not user:
        return  # Skip if no user (anonymous/system action)

    last_activity = UserActivity.objects.filter(user=user).order_by('-timestamp').first()
    if last_activity and last_activity.action == action and last_activity.method == method \
       and last_activity.path == path and last_activity.ip_address == ip:
        return  # Skip duplicate
    UserActivity.objects.create(
        user=user,
        action=action,
        method=method,
        path=path,
        ip_address=ip,
        timestamp=now()
    )


# ------------------- LOGIN -------------------
@receiver(user_logged_in)
def handle_user_login(sender, request, user, **kwargs):
    if is_running_migrations():
        return


# ------------------- LOGOUT -------------------
@receiver(user_logged_out)
def handle_user_logout(sender, request, user, **kwargs):
    if is_running_migrations():
        return

# ------------------- CREATE / UPDATE -------------------
@receiver(post_save)
def log_model_save(sender, instance, created, **kwargs):
    if is_running_migrations():
        return
    if sender.__name__ == 'AuditLog':
        return

    user = getattr(instance, '_audit_user', None)
    ip = getattr(instance, '_audit_ip', None)
    action = 'Created' if created else 'Updated'

    # Audit log
    log_audit(user, action.upper(), get_model_name(instance), instance.pk, description=str(instance), ip_address=ip)

    # User activity
    create_activity_if_not_duplicate(user, f"{action} {get_model_name(instance)}", "SYSTEM", "-", ip)


# ------------------- DELETE -------------------
@receiver(post_delete)
def log_model_delete(sender, instance, **kwargs):
    if is_running_migrations():
        return
    if sender.__name__ == 'AuditLog':
        return

    user = getattr(instance, '_audit_user', None)
    ip = getattr(instance, '_audit_ip', None)

    # Audit log
    log_audit(user, 'DELETE', get_model_name(instance), instance.pk, description=str(instance), ip_address=ip)

    # User activity
    create_activity_if_not_duplicate(user, f"Deleted {get_model_name(instance)}", "SYSTEM", "-", ip)
