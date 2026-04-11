from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from . import views

urlpatterns = [
    # JWT Auth — replaces old login/logout
    path('token/', TokenObtainPairView.as_view(), name='token-obtain'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token-refresh'),

    # Users
    path('register/', views.RegisterView.as_view(), name='register'),
    path('users/', views.UserListView.as_view(), name='user-list'),
    path('users/<int:pk>/', views.UserDetailView.as_view(), name='user-detail'),
    path('branches/', views.BranchListView.as_view(), name='branch-list'),
    path('me/', views.MeView.as_view(), name='me'),
]