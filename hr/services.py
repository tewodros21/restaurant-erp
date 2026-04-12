from .models import AttendanceRecord, PayrollRecord, EmployeeProfile
from django.utils import timezone
from decimal import Decimal


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


def generate_payroll(employee, month, year):
    try:
        profile = employee.profile
    except Exception:
        return None, "Employee profile not found"

    attendance_records = AttendanceRecord.objects.filter(
        employee    = employee,
        date__month = month,
        date__year  = year
    )

    total_overtime = sum(r.overtime_hours for r in attendance_records)

    absent_days = attendance_records.filter(status='ABSENT').count()

    #Fix — ensure base_salary is Decimal
    base_salary = Decimal(str(profile.base_salary))
    daily_rate  = base_salary / Decimal('30')
    deductions  = Decimal(str(absent_days)) * daily_rate

    hourly_rate  = base_salary / Decimal('240')  # 30 days * 8 hours
    overtime_pay = Decimal(str(total_overtime)) * hourly_rate * Decimal(str(profile.overtime_rate))

    net_salary = base_salary + overtime_pay - deductions

    payroll, created = PayrollRecord.objects.update_or_create(
        employee = employee,
        month    = month,
        year     = year,
        defaults = {
            'base_salary':    base_salary,
            'overtime_hours': Decimal(str(total_overtime)),
            'overtime_pay':   overtime_pay,
            'deductions':     deductions,
            'net_salary':     net_salary,
            'status':         'DRAFT'
        }
    )

    return payroll, "Payroll generated successfully"