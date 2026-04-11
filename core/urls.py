from django.urls import path
from . import views

urlpatterns = [
    path('backup/trigger/', views.TriggerBackupView.as_view(), name='trigger-backup'),
    path('backup/list/', views.ListBackupsView.as_view(), name='list-backups'),
]