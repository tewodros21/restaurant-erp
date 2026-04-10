from django.urls import path
from . import views

urlpatterns = [
    # Dashboard
    path('dashboard/', views.DashboardView.as_view(), name='dashboard'),

    # Expenses
    path('expenses/categories/', views.ExpenseCategoryListView.as_view(), name='expense-categories'),
    path('expenses/', views.ExpenseListView.as_view(), name='expense-list'),
    path('expenses/<int:pk>/', views.ExpenseDetailView.as_view(), name='expense-detail'),
    path('expenses/<int:pk>/approve/', views.ApproveExpenseView.as_view(), name='approve-expense'),

    # Reports
    path('reports/daily/', views.DailyReportListView.as_view(), name='daily-reports'),
    path('reports/daily/generate/', views.GenerateDailyReportView.as_view(), name='generate-daily-report'),
    path('reports/monthly/', views.MonthlySummaryView.as_view(), name='monthly-summary'),
    path('reports/annual/', views.AnnualSummaryView.as_view(), name='annual-summary'),
    path('reports/top-items/', views.TopSellingItemsView.as_view(), name='top-selling-items'),
]