from DBMS.models import AuditLog

def log_audit(user, action, model_name, object_id, description='', ip_address=None):
    AuditLog.objects.create(
        user=user,
        action=action,
        model_name=model_name,
        object_id=object_id,
        description=description,
        ip_address=ip_address
    )
