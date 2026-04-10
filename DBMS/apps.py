from django.apps import AppConfig


class DbmsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'DBMS'
    
class DbmsConfig(AppConfig):
    name = 'DBMS'

    def ready(self):
        import DBMS.signals  # Import signals so they get registered
