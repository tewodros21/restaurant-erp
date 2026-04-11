from rest_framework.views import APIView
from rest_framework.response import Response
from accounts.permissions import IsAdmin
from .tasks import backup_database
import os
from django.conf import settings


class TriggerBackupView(APIView):
    """Manually trigger a database backup"""
    permission_classes = [IsAdmin]

    def post(self, request):
        backup_database.delay()  # runs async via Celery
        return Response({'message': 'Backup started in background'})


class ListBackupsView(APIView):
    """List all available backups"""
    permission_classes = [IsAdmin]

    def get(self, request):
        backup_dir = os.path.join(settings.BASE_DIR, 'backups')
        if not os.path.exists(backup_dir):
            return Response({'backups': []})

        files = []
        for filename in sorted(os.listdir(backup_dir), reverse=True):
            filepath = os.path.join(backup_dir, filename)
            files.append({
                'filename': filename,
                'size_mb':  round(os.path.getsize(filepath) / 1024 / 1024, 2),
                'created':  os.path.getmtime(filepath)
            })
        return Response({'backups': files})