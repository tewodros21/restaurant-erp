from django.urls import path
from . import views

urlpatterns = [
    # Categories
    path('categories/', views.AssetCategoryListView.as_view(), name='asset-category-list'),

    # Assets
    path('', views.AssetListView.as_view(), name='asset-list'),
    path('<int:pk>/', views.AssetDetailView.as_view(), name='asset-detail'),
    path('<int:pk>/qr/', views.GenerateAssetQRView.as_view(), name='asset-qr'),

    # Depreciation
    path('depreciation/apply/', views.ApplyDepreciationView.as_view(), name='apply-depreciation'),
    path('depreciation/records/', views.DepreciationRecordListView.as_view(), name='depreciation-records'),

    # Maintenance
    path('maintenance/schedules/', views.MaintenanceScheduleListView.as_view(), name='maintenance-schedules'),
    path('maintenance/schedules/<int:pk>/', views.MaintenanceScheduleDetailView.as_view(), name='maintenance-schedule-detail'),
    path('maintenance/upcoming/', views.UpcomingMaintenanceView.as_view(), name='upcoming-maintenance'),
    path('maintenance/logs/', views.MaintenanceLogListView.as_view(), name='maintenance-logs'),
    path('maintenance/logs/<int:pk>/', views.MaintenanceLogDetailView.as_view(), name='maintenance-log-detail'),
]