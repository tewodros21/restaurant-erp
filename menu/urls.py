from django.urls import path
from . import views

urlpatterns = [
    path('', views.MenuDetailView.as_view(), name='menu-detail'),
    path('public/<int:branch_id>/', views.PublicMenuView.as_view(), name='public-menu'),
    path('sections/', views.MenuSectionListView.as_view(), name='section-list'),
    path('sections/<int:pk>/', views.MenuSectionDetailView.as_view(), name='section-detail'),
    path('items/', views.MenuItemListView.as_view(), name='item-list'),
    path('items/<int:pk>/', views.MenuItemDetailView.as_view(), name='item-detail'),
]