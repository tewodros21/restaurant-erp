import pytest
from finance.services import generate_daily_report, get_monthly_summary
from finance.models import Expense
from tests.factories import BranchFactory


@pytest.mark.django_db
class TestFinanceReports:

    def test_generate_daily_report(self, branch):
        from django.utils import timezone
        report = generate_daily_report(branch, timezone.now().date())
        assert report is not None
        assert report.total_sales >= 0
        assert report.branch == branch

    def test_monthly_summary_structure(self, branch):
        data = get_monthly_summary(branch, month=1, year=2026)
        assert 'total_sales' in data
        assert 'total_expenses' in data
        assert 'net_profit' in data
        assert 'payroll_cost' in data

    def test_expense_creation(self, manager_client, manager_user):
        from finance.models import ExpenseCategory
        from django.urls import reverse

        category = ExpenseCategory.objects.create(name='Utilities')
        url      = reverse('expense-list')
        data     = {
            'category':    category.id,
            'title':       'Electricity Bill',
            'amount':      '1500.00',
            'date':        '2026-04-01',
            'description': 'April electricity'
        }
        response = manager_client.post(url, data)

        # Print error to see what's wrong
        print("\nExpense API error:", response.data)

        assert response.status_code == 201