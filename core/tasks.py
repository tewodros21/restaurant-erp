from celery import shared_task
from django.conf import settings
import subprocess
import os
from datetime import datetime


@shared_task
def backup_database():
    """
    Daily backup of PostgreSQL database.
    Saves to /backups/ folder with timestamp.
    """
    timestamp   = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_dir  = os.path.join(settings.BASE_DIR, 'backups')
    backup_file = os.path.join(backup_dir, f'backup_{timestamp}.sql')

    # Create backups directory if it doesn't exist
    os.makedirs(backup_dir, exist_ok=True)

    db = settings.DATABASES['default']

    # Run pg_dump
    result = subprocess.run([
        'pg_dump',
        f'--host={db["HOST"]}',
        f'--port={db["PORT"]}',
        f'--username={db["USER"]}',
        f'--dbname={db["NAME"]}',
        f'--file={backup_file}',
        '--format=plain',
        '--no-password'
    ], env={
        **os.environ,
        'PGPASSWORD': db['PASSWORD']
    }, capture_output=True, text=True)

    if result.returncode == 0:
        # Clean up old backups — keep last 30 days
        cleanup_old_backups(backup_dir, keep_days=30)
        return f"Backup successful: {backup_file}"
    else:
        return f"Backup failed: {result.stderr}"


def cleanup_old_backups(backup_dir, keep_days=30):
    """Delete backups older than keep_days"""
    import time
    now         = time.time()
    cutoff      = now - (keep_days * 86400)

    for filename in os.listdir(backup_dir):
        filepath = os.path.join(backup_dir, filename)
        if os.path.isfile(filepath):
            if os.path.getmtime(filepath) < cutoff:
                os.remove(filepath)


@shared_task
def restore_database(backup_file):
    """Restore database from a backup file"""
    db = settings.DATABASES['default']

    result = subprocess.run([
        'psql',
        f'--host={db["HOST"]}',
        f'--port={db["PORT"]}',
        f'--username={db["USER"]}',
        f'--dbname={db["NAME"]}',
        f'--file={backup_file}',
    ], env={
        **os.environ,
        'PGPASSWORD': db['PASSWORD']
    }, capture_output=True, text=True)

    if result.returncode == 0:
        return f"Restore successful from: {backup_file}"
    else:
        return f"Restore failed: {result.stderr}"