#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""

import os
import sys

def main():
    """Run administrative tasks."""
    # Set the default Django settings module for the 'manage.py' commands
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'system2.settings')

    try:
        from django.core.management import execute_from_command_line

        # --- START: auto-create DB and run migrations ---
        try:
            # Ensure we can find startup.py in project root
            project_root = os.path.dirname(os.path.abspath(__file__))
            sys.path.append(project_root)

            from startup import prepare_database
            prepare_database()  # create DB and tables if missing
        except ModuleNotFoundError:
            # If startup.py is missing, just continue
            pass
        except Exception as e:
            print(f"⚠️ Error during auto-migration: {e}")
        # --- END: auto-create DB and run migrations ---

    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Make sure Django is installed and "
            "available on your PYTHONPATH environment variable, or "
            "activate your virtual environment."
        ) from exc

    # Execute the command line utility
    execute_from_command_line(sys.argv)

if __name__ == "__main__":
    main()
