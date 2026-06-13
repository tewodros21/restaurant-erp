from django.db.models import Sum, Count, F
from django.utils import timezone
from decimal import Decimal
from .models import DailyReport, Expense
from pos.models import Order
from hr.models import PayrollRecord


def _payment_method(order):
    """Return the payment method for an order's bill, or None if not paid."""
    bill = getattr(order, 'bill', None)
    if not bill:
        return None
    payment = getattr(bill, 'payment', None)
    return payment.method if payment else None


def generate_daily_report(branch, date=None):
    """Generate daily financial summary for a branch"""
    if not branch:
        return None

    if not date:
        date = timezone.now().date()

    # Get all completed orders for the day (prefetch the lines used by
    # Order.total_price and the bill/payment used for the method breakdown).
    orders = Order.objects.filter(
        branch     = branch,
        status     = 'COMPLETED',
        created_at__date = date
    ).select_related('bill__payment').prefetch_related('meals__items')

    # Calculate sales totals
    total_sales  = sum((o.total_price for o in orders), Decimal('0.00'))
    total_orders = orders.count()

    # Payment method breakdown (Payment.method lives on Bill.payment)
    cash_sales     = sum((o.total_price for o in orders if _payment_method(o) == 'CASH'), Decimal('0.00'))
    card_sales     = sum((o.total_price for o in orders if _payment_method(o) == 'CREDIT_CARD'), Decimal('0.00'))
    transfer_sales = sum((o.total_price for o in orders if _payment_method(o) == 'BANK_TRANSFER'), Decimal('0.00'))
    digital_sales  = sum((o.total_price for o in orders if _payment_method(o) in ('TELEBIRR', 'DIGITAL_WALLET')), Decimal('0.00'))

    # Get total expenses for the day
    total_expenses = Expense.objects.filter(
        branch = branch,
        date   = date,
        status = 'APPROVED'
    ).aggregate(total=Sum('amount'))['total'] or Decimal('0')

    net_profit = total_sales - total_expenses

    # Save or update daily report
    report, _ = DailyReport.objects.update_or_create(
        branch = branch,
        date   = date,
        defaults = {
            'total_sales':          total_sales,
            'total_orders':         total_orders,
            'total_expenses':       total_expenses,
            'cash_sales':           cash_sales,
            'card_sales':           card_sales,
            'transfer_sales':       transfer_sales,
            'digital_wallet_sales': digital_sales,
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

    agg = reports.aggregate(
        total_sales    = Sum('total_sales'),
        total_expenses = Sum('total_expenses'),
        total_orders   = Sum('total_orders'),
        net_profit     = Sum('net_profit'),
    )
    total_sales    = agg['total_sales'] or Decimal('0.00')
    total_expenses = agg['total_expenses'] or Decimal('0.00')
    total_orders   = agg['total_orders'] or 0
    net_profit     = agg['net_profit'] or Decimal('0.00')

    # Payroll cost for the month
    payroll_cost = PayrollRecord.objects.filter(
        employee__branch = branch,
        month            = month,
        year             = year,
        status           = 'PAID'
    ).aggregate(t=Sum('net_salary'))['t'] or Decimal('0.00')

    return {
        'month':          month,
        'year':           year,
        'total_sales':    total_sales,
        'total_expenses': total_expenses,
        'total_orders':   total_orders,
        'payroll_cost':   payroll_cost,
        'net_profit':     net_profit - payroll_cost,
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

    items = MealItem.objects.filter(
        meal__order__branch        = branch,
        meal__order__status        = 'COMPLETED',
        meal__order__created_at__date__gte = date_from,
        meal__order__created_at__date__lte = date_to
    ).exclude(
        status = MealItem.Status.CANCELLED
    ).values(
        'menu_item__name',
        'menu_item__id'
    ).annotate(
        total_quantity = Sum('quantity'),
        total_revenue  = Sum(F('unit_price') * F('quantity')),
        order_count    = Count('meal__order', distinct=True)
    ).order_by('-total_quantity')[:limit]

    return list(items)