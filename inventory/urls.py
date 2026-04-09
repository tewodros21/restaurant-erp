from django.urls import path
from . import views

urlpatterns = [
    # Categories & Units
    path('categories/', views.CategoryListView.as_view(), name='category-list'),
    path('units/', views.UnitListView.as_view(), name='unit-list'),

    # Ingredients / Stock
    path('ingredients/', views.IngredientListView.as_view(), name='ingredient-list'),
    path('ingredients/<int:pk>/', views.IngredientDetailView.as_view(), name='ingredient-detail'),
    path('ingredients/<int:ingredient_id>/add-stock/', views.AddStockView.as_view(), name='add-stock'),

    # Recipes
    path('recipes/', views.RecipeListView.as_view(), name='recipe-list'),
    path('recipes/<int:pk>/', views.RecipeDetailView.as_view(), name='recipe-detail'),
    path('recipes/ingredients/', views.AddRecipeIngredientView.as_view(), name='add-recipe-ingredient'),

    # Transactions & Wastage
    path('transactions/', views.StockTransactionListView.as_view(), name='stock-transactions'),
    path('wastage/', views.WastageLogListView.as_view(), name='wastage-log'),

    # Alerts
    path('alerts/low-stock/', views.LowStockAlertView.as_view(), name='low-stock-alert'),
    path('alerts/expired/', views.ExpiredIngredientView.as_view(), name='expired-ingredients'),
]