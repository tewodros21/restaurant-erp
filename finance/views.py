from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from django.utils import timezone
from datetime import date
from .models import ExpenseCategory, Expense, DailyReport
from .serializers import ExpenseCategorySerializer, ExpenseSerializer, DailyReportSerializer
from .services import (
    generate_daily_report,
    get_monthly_summary,
    get_annual_summary,
    get_top_selling_items
)
from accounts.permissions import IsManager


class ExpenseCategoryListView(generics.ListCreateAPIView):
    serializer_class   = ExpenseCategorySerializer
    permission_classes = [IsManager]
    queryset           = ExpenseCategory.objects.all()


class ExpenseListView(generics.ListCreateAPIView):
    serializer_class   = ExpenseSerializer
    permission_classes = [IsManager]

    def get_queryset(self):
        qs    = Expense.objects.filter(branch=self.request.user.branch)
        month = self.request.query_params.get('month')
        year  = self.request.query_params.get('year')
        if month and year:
            qs = qs.filter(date__month=month, date__year=year)
        return qs.order_by('-date')

    def perform_create(self, serializer):
        serializer.save(
            branch     = self.request.user.branch,
            created_by = self.request.user
        )


class ExpenseDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class   = ExpenseSerializer
    permission_classes = [IsManager]

    def get_queryset(self):
        return Expense.objects.filter(branch=self.request.user.branch)


class ApproveExpenseView(APIView):
    """Manager approves an expense"""
    permission_classes = [IsManager]

    def patch(self, request, pk):
        expense    = get_object_or_404(Expense, pk=pk, branch=request.user.branch)
        new_status = request.data.get('status')

        if new_status not in ['APPROVED', 'REJECTED']:
            return Response(
                {'error': 'Status must be APPROVED or REJECTED'},
                status=status.HTTP_400_BAD_REQUEST
            )

        expense.status      = new_status
        expense.approved_by = request.user
        expense.save()
        return Response(ExpenseSerializer(expense).data)


class GenerateDailyReportView(APIView):
    """Generate or refresh daily report"""
    permission_classes = [IsManager]

    def post(self, request):
        date_str = request.data.get('date')
        if date_str:
            report_date = date.fromisoformat(date_str)
        else:
            report_date = timezone.now().date()

        report = generate_daily_report(request.user.branch, report_date)
        return Response(DailyReportSerializer(report).data)


class DailyReportListView(generics.ListAPIView):
    """List all daily reports for branch"""
    serializer_class   = DailyReportSerializer
    permission_classes = [IsManager]

    def get_queryset(self):
        qs    = DailyReport.objects.filter(branch=self.request.user.branch)
        month = self.request.query_params.get('month')
        year  = self.request.query_params.get('year')
        if month and year:
            qs = qs.filter(date__month=month, date__year=year)
        return qs


class MonthlySummaryView(APIView):
    """Get monthly P&L summary"""
    permission_classes = [IsManager]

    def get(self, request):
        month = int(request.query_params.get('month', timezone.now().month))
        year  = int(request.query_params.get('year', timezone.now().year))
        data  = get_monthly_summary(request.user.branch, month, year)
        return Response(data)


class AnnualSummaryView(APIView):
    """Get full year P&L summary"""
    permission_classes = [IsManager]

    def get(self, request):
        year = int(request.query_params.get('year', timezone.now().year))
        data = get_annual_summary(request.user.branch, year)
        return Response(data)


class TopSellingItemsView(APIView):
    """Get top selling menu items"""
    permission_classes = [IsManager]

    def get(self, request):
        today     = timezone.now().date()
        date_from = request.query_params.get('from', str(today.replace(day=1)))
        date_to   = request.query_params.get('to', str(today))
        limit     = int(request.query_params.get('limit', 10))

        items = get_top_selling_items(
            request.user.branch,
            date_from,
            date_to,
            limit
        )
        return Response(items)


class DashboardView(APIView):
    """Main dashboard — today's snapshot"""
    permission_classes = [IsManager]

    def get(self, request):
        branch = request.user.branch
        if not branch:
            return Response(
                {'error': 'User has no assigned branch. Please contact an admin.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        today  = timezone.now().date()

        # Generate today's report
        report = generate_daily_report(branch, today)
        if not report:
            return Response(
                {'error': 'Failed to generate summary for this branch.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Get pending expenses
        pending_expenses = Expense.objects.filter(
            branch=branch, status='PENDING'
        ).count()

        # Get low stock count
        from inventory.models import Ingredient
        ingredients  = Ingredient.objects.filter(branch=branch)
        low_stock    = sum(1 for i in ingredients if i.is_low_stock)
        expired      = sum(1 for i in ingredients if i.is_expired)

        # Get upcoming maintenance
        from assets.services import get_upcoming_maintenance
        upcoming_maintenance = get_upcoming_maintenance(branch, days=7).count()

        return Response({
            'today':                str(today),
            'total_sales':          report.total_sales,
            'total_orders':         report.total_orders,
            'net_profit':           report.net_profit,
            'pending_expenses':     pending_expenses,
            'low_stock_alerts':     low_stock,
            'expired_ingredients':  expired,
            'upcoming_maintenance': upcoming_maintenance,
            'payment_breakdown': {
                'cash':           report.cash_sales,
                'card':           report.card_sales,
                'bank_transfer':  report.transfer_sales,
                'digital_wallet': report.digital_wallet_sales
            }
        })