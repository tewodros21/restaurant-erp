from .models import AttendanceRecord, PayrollRecord, EmployeeProfile, LeaveRequest
from django.utils import timezone
from decimal import Decimal
from calendar import monthrange
from datetime import date

# Payroll assumes a simplified fixed-length month / working day. Surface these
# as named constants rather than burying 30 / 240 in the arithmetic.
WORKING_DAYS_PER_MONTH = Decimal('30')
HOURS_PER_DAY = Decimal('8')
CENTS = Decimal('0.01')


def _unpaid_leave_days(employee, month, year):
    """Count approved UNPAID leave days that fall within the given month."""
    month_start = date(year, month, 1)
    month_end   = date(year, month, monthrange(year, month)[1])
    days = 0
    requests = LeaveRequest.objects.filter(
        employee   = employee,
        status     = 'APPROVED',
        leave_type = 'UNPAID',
        start_date__lte = month_end,
        end_date__gte   = month_start,
    )
    for lr in requests:
        overlap_start = max(lr.start_date, month_start)
        overlap_end   = min(lr.end_date, month_end)
        days += (overlap_end - overlap_start).days + 1
    return days


def clock_in(employee):
    """Employee clocks in"""
    today = timezone.now().date()

    record, created = AttendanceRecord.objects.get_or_create(
        employee = employee,
        date     = today,
        defaults = {
            'clock_in': timezone.now(),
            'status':   AttendanceRecord.Status.PRESENT
        }
    )

    if not created and record.clock_in:
        return None, "Already clocked in today"

    if not created:
        record.clock_in = timezone.now()
        record.save()

    return record, "Clocked in successfully"


def clock_out(employee):
    """Employee clocks out"""
    today = timezone.now().date()

    try:
        record = AttendanceRecord.objects.get(employee=employee, date=today)
        if record.clock_out:
            return None, "Already clocked out today"
        record.clock_out = timezone.now()
        record.save()
        return record, f"Clocked out. Hours worked: {record.hours_worked}"
    except AttendanceRecord.DoesNotExist:
        return None, "No clock-in record found for today"


def generate_payroll(employee, month, year, bonus=None):
    try:
        profile = employee.profile
    except Exception:
        return None, "Employee profile not found"

    attendance_records = AttendanceRecord.objects.filter(
        employee    = employee,
        date__month = month,
        date__year  = year
    )

    total_overtime = sum((r.overtime_hours for r in attendance_records), 0)

    absent_days = attendance_records.filter(status='ABSENT').count()
    unpaid_days = _unpaid_leave_days(employee, month, year)
    unpaid_total_days = absent_days + unpaid_days

    base_salary = Decimal(str(profile.base_salary))
    daily_rate  = base_salary / WORKING_DAYS_PER_MONTH
    deductions  = (Decimal(unpaid_total_days) * daily_rate).quantize(CENTS)

    hourly_rate  = base_salary / (WORKING_DAYS_PER_MONTH * HOURS_PER_DAY)
    overtime_pay = (
        Decimal(str(total_overtime)) * hourly_rate * Decimal(str(profile.overtime_rate))
    ).quantize(CENTS)

    # Preserve any bonus already recorded unless a new one is supplied.
    if bonus is None:
        existing = PayrollRecord.objects.filter(
            employee=employee, month=month, year=year
        ).first()
        bonus_amount = existing.bonus if existing else Decimal('0')
    else:
        bonus_amount = Decimal(str(bonus))

    net_salary = (base_salary + overtime_pay + bonus_amount - deductions).quantize(CENTS)

    payroll, created = PayrollRecord.objects.update_or_create(
        employee = employee,
        month    = month,
        year     = year,
        defaults = {
            'base_salary':    base_salary,
            'overtime_hours': Decimal(str(total_overtime)),
            'overtime_pay':   overtime_pay,
            'deductions':     deductions,
            'bonus':          bonus_amount,
            'net_salary':     net_salary,
            'status':         'DRAFT'
        }
    )

    return payroll, "Payroll generated successfully"