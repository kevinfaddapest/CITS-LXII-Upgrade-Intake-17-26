#!/usr/bin/env python
import os
import django
from django.core.management import call_command

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "system2.settings")

django.setup()

print("Applying migrations...")
call_command("migrate", interactive = False)

print("Migrations complete.")
