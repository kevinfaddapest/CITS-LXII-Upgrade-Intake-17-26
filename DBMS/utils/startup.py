# startup.py
import os
from django.core.management import call_command

def prepare_database():
    """
    Auto-create database tables if missing by running migrations.
    """
    # Only run migrate if database file doesn't exist
    from pathlib import Path
    from django.conf import settings

    db_file = Path(settings.DATABASES['default']['NAME'])
    if not db_file.exists():
        print("⚡ Database not found. Running migrations...")
        call_command("migrate", interactive=False)
        print("✅ Database and tables created!")
