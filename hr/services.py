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
    """
    Auto-calculate payroll for an employee for a given month/year.
    """
    try:
        profile = employee.profile
    except Exception:
        return None, "Employee profile not found"

    # Get all attendance for the month
    attendance_records = AttendanceRecord.objects.filter(
        employee = employee,
        date__month = month,
        date__year  = year
    )

    # Calculate total overtime hours
    total_overtime = sum(r.overtime_hours for r in attendance_records)

    # Calculate deductions (absent days)
    absent_days = attendance_records.filter(status='ABSENT').count()
    daily_rate  = profile.base_salary / 30
    deductions  = Decimal(str(absent_days)) * daily_rate

    # Calculate overtime pay
    hourly_rate  = profile.base_salary / (30 * 8)  # monthly / (days * hours)
    overtime_pay = Decimal(str(total_overtime)) * hourly_rate * profile.overtime_rate

    # Calculate net salary
    net_salary = profile.base_salary + overtime_pay - deductions

    # Create or update payroll record
    payroll, created = PayrollRecord.objects.update_or_create(
        employee = employee,
        month    = month,
        year     = year,
        defaults = {
            'base_salary':    profile.base_salary,
            'overtime_hours': Decimal(str(total_overtime)),
            'overtime_pay':   overtime_pay,
            'deductions':     deductions,
            'net_salary':     net_salary,
            'status':         'DRAFT'
        }
    )

    return payroll, "Payroll generated successfully"