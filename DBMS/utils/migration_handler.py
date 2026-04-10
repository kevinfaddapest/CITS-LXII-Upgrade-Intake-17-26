import sys
import os
from django.core.management import call_command
from django.db import connections
from django.db.utils import OperationalError
from django.db.migrations.executor import MigrationExecutor

def run_pending_migrations():
    """
    Automatically run makemigrations + migrate if:
    - SQLite DB is empty/new
    - There are unapplied migrations
    """
    if 'migrate' in sys.argv or 'makemigrations' in sys.argv:
        return  # Don't recurse

    try:
        db_conn = connections['default']
        db_conn.ensure_connection()
    except OperationalError:
        return  # DB not ready

    try:
        executor = MigrationExecutor(db_conn)
        targets = executor.loader.graph.leaf_nodes()
        plan = executor.migration_plan(targets)

        if plan:  # There are unapplied migrations
            print("[Migration Handler] Applying pending migrations...")
            call_command("makemigrations", interactive=False, verbosity=0)
            call_command("migrate", interactive=False, verbosity=0)
        else:
            # Optional: detect brand-new SQLite file with no tables
            if db_conn.introspection.table_names() == []:
                print("[Migration Handler] Fresh database detected. Running initial migrations...")
                call_command("makemigrations", interactive=False, verbosity=0)
                call_command("migrate", interactive=False, verbosity=0)

    except Exception as e:
        print(f"[Migration Handler] Skipped due to: {e}")
