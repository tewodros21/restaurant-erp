from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

# Swagger schema view
schema_view = get_schema_view(
    openapi.Info(
        title              = "Restaurant ERP API",
        default_version    = 'v1',
        description        = "Complete Restaurant ERP System API Documentation",
        contact            = openapi.Contact(email="dev@restauranterp.com"),
        license            = openapi.License(name="Private"),
    ),
    public     = True,
    permission_classes = [permissions.AllowAny],
)

urlpatterns = [
    # Admin
    path('admin/', admin.site.urls),

    # API Docs
    path('docs/', schema_view.with_ui('swagger', cache_timeout=0), name='swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='redoc'),

    # API Routes
    path('api/accounts/',      include('accounts.urls')),
    path('api/menu/',          include('menu.urls')),
    path('api/tables/',        include('tables.urls')),
    path('api/pos/',           include('pos.urls')),
    path('api/inventory/',     include('inventory.urls')),
    path('api/hr/',            include('hr.urls')),
    path('api/assets/',        include('assets.urls')),
    path('api/finance/',       include('finance.urls')),
    path('api/notifications/', include('notifications.urls')),
    path('api/core/',          include('core.urls')),

] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)