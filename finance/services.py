from django.db.models import Sum, Count, Q
from django.utils import timezone
from decimal import Decimal
from .models import DailyReport, Expense
from pos.models import Order
from hr.models import PayrollRecord


def generate_daily_report(branch, date=None):
    """Generate daily financial summary for a branch"""
    if not date:
        date = timezone.now().date()

    # Get all completed orders for the day
    orders = Order.objects.filter(
        branch     = branch,
        status     = 'COMPLETED',
        created_at__date = date
    )

    # Calculate sales totals
    total_sales  = sum(o.total_price for o in orders)
    total_orders = orders.count()

    # Payment method breakdown
    cash_sales     = sum(o.total_price for o in orders if hasattr(o, 'bill') and o.bill.payment_method == 'CASH')
    card_sales     = sum(o.total_price for o in orders if hasattr(o, 'bill') and o.bill.payment_method == 'CARD')
    transfer_sales = sum(o.total_price for o in orders if hasattr(o, 'bill') and o.bill.payment_method == 'TRANSFER')
    digital_sales  = sum(o.total_price for o in orders if hasattr(o, 'bill') and o.bill.payment_method == 'DIGITAL')

    # Get total expenses for the day
    total_expenses = Expense.objects.filter(
        branch = branch,
        date   = date,
        status = 'APPROVED'
    ).aggregate(total=Sum('amount'))['total'] or Decimal('0')

    net_profit = Decimal(str(total_sales)) - total_expenses

    # Save or update daily report
    report, _ = DailyReport.objects.update_or_create(
        branch = branch,
        date   = date,
        defaults = {
            'total_sales':          Decimal(str(total_sales)),
            'total_orders':         total_orders,
            'total_expenses':       total_expenses,
            'cash_sales':           Decimal(str(cash_sales)),
            'card_sales':           Decimal(str(card_sales)),
            'transfer_sales':       Decimal(str(transfer_sales)),
            'digital_wallet_sales': Decimal(str(digital_sales)),
            'net_profit':           net_profit
        }
    )
    return report


def get_monthly_summary(branch, month, year):
    """Get monthly financial summary"""
    reports = DailyReport.objects.filter(
        branch          = branch,
        date__month     = month,
        date__year      = year
    )

    total_sales    = reports.aggregate(t=Sum('total_sales'))['t'] or 0
    total_expenses = reports.aggregate(t=Sum('total_expenses'))['t'] or 0
    total_orders   = reports.aggregate(t=Sum('total_orders'))['t'] or 0
    net_profit     = reports.aggregate(t=Sum('net_profit'))['t'] or 0

    # Payroll cost for the month
    payroll_cost = PayrollRecord.objects.filter(
        employee__branch = branch,
        month            = month,
        year             = year,
        status           = 'PAID'
    ).aggregate(t=Sum('net_salary'))['t'] or 0

    return {
        'month':          month,
        'year':           year,
        'total_sales':    total_sales,
        'total_expenses': total_expenses,
        'total_orders':   total_orders,
        'payroll_cost':   payroll_cost,
        'net_profit':     float(net_profit) - float(payroll_cost),
        'daily_reports':  reports.count()
    }


def get_annual_summary(branch, year):
    """Get annual financial summary broken down by month"""
    monthly_data = []
    for month in range(1, 13):
        data = get_monthly_summary(branch, month, year)
        monthly_data.append(data)

    total_annual_sales  = sum(m['total_sales'] for m in monthly_data)
    total_annual_profit = sum(m['net_profit'] for m in monthly_data)

    return {
        'year':                 year,
        'monthly_breakdown':    monthly_data,
        'total_annual_sales':   total_annual_sales,
        'total_annual_profit':  total_annual_profit
    }


def get_top_selling_items(branch, date_from, date_to, limit=10):
    """Get top selling menu items in a date range"""
    from pos.models import MealItem
    from django.db.models import Sum, Count

    items = MealItem.objects.filter(
        meal__order__branch        = branch,
        meal__order__status        = 'COMPLETED',
        meal__order__created_at__date__gte = date_from,
        meal__order__created_at__date__lte = date_to
    ).values(
        'menu_item__name',
        'menu_item__id'
    ).annotate(
        total_quantity = Sum('quantity'),
        total_revenue  = Sum('unit_price'),
        order_count    = Count('id')
    ).order_by('-total_quantity')[:limit]

    return list(items)