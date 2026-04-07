from django.urls import path
from . import views

urlpatterns = [
    path('', views.TableListView.as_view(), name='table-list'),
    path('<int:pk>/', views.TableDetailView.as_view(), name='table-detail'),
    path('available/', views.AvailableTablesView.as_view(), name='available-tables'),
    path('<int:pk>/status/', views.UpdateTableStatusView.as_view(), name='update-table-status'),
    path('<int:pk>/qr/', views.GenerateTableQRView.as_view(), name='generate-table-qr'),
    path('arrangements/', views.SeatingArrangementListView.as_view(), name='seating-arrangements'),
]