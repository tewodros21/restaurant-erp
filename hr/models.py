from django.db import models
from accounts.models import User, Branch


class Department(models.Model):
    branch      = models.ForeignKey(Branch, on_delete=models.CASCADE, related_name='departments')
    name        = models.CharField(max_length=100)  # e.g. Kitchen, Service, Bar
    description = models.TextField(blank=True)

    def __str__(self):
        return f"{self.branch.name} - {self.name}"


class EmployeeProfile(models.Model):
    class ContractType(models.TextChoices):
        FULL_TIME  = 'FULL_TIME',  'Full Time'
        PART_TIME  = 'PART_TIME',  'Part Time'
        CONTRACT   = 'CONTRACT',   'Contract'
        INTERN     = 'INTERN',     'Intern'

    user            = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    department      = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True)
    contract_type   = models.CharField(max_length=20, choices=ContractType.choices, default=ContractType.FULL_TIME)
    date_joined     = models.DateField()
    base_salary     = models.DecimalField(max_digits=10, decimal_places=2)
    overtime_rate   = models.DecimalField(max_digits=5, decimal_places=2, default=1.5)  # multiplier
    national_id     = models.CharField(max_length=50, blank=True)
    emergency_contact_name  = models.CharField(max_length=100, blank=True)
    emergency_contact_phone = models.CharField(max_length=20, blank=True)
    bank_account    = models.CharField(max_length=50, blank=True)
    is_active       = models.BooleanField(default=True)
    notes           = models.TextField(blank=True)

    def __str__(self):
        return f"{self.user.get_full_name()} - {self.contract_type}"


class AttendanceRecord(models.Model):
    class Status(models.TextChoices):
        PRESENT = 'PRESENT', 'Present'
        ABSENT  = 'ABSENT',  'Absent'
        LATE    = 'LATE',    'Late'
        HALF_DAY = 'HALF_DAY', 'Half Day'
        ON_LEAVE = 'ON_LEAVE', 'On Leave'

    employee    = models.ForeignKey(User, on_delete=models.CASCADE, related_name='attendance')
    date        = models.DateField()
    clock_in    = models.DateTimeField(null=True, blank=True)
    clock_out   = models.DateTimeField(null=True, blank=True)
    status      = models.CharField(max_length=20, choices=Status.choices, default=Status.PRESENT)
    notes       = models.TextField(blank=True)

    class Meta:
        unique_together = ['employee', 'date']
        ordering        = ['-date']

    def __str__(self):
        return f"{self.employee.get_full_name()} - {self.date} ({self.status})"

    @property
    def hours_worked(self):
        if self.clock_in and self.clock_out:
            delta = self.clock_out - self.clock_in
            return round(delta.total_seconds() / 3600, 2)
        return 0

    @property
    def overtime_hours(self):
        standard_hours = 8
        worked = self.hours_worked
        return max(0, worked - standard_hours)


class LeaveRequest(models.Model):
    class LeaveType(models.TextChoices):
        ANNUAL   = 'ANNUAL',   'Annual Leave'
        SICK     = 'SICK',     'Sick Leave'
        UNPAID   = 'UNPAID',   'Unpaid Leave'
        MATERNITY = 'MATERNITY', 'Maternity Leave'
        OTHER    = 'OTHER',    'Other'

    class Status(models.TextChoices):
        PENDING  = 'PENDING',  'Pending'
        APPROVED = 'APPROVED', 'Approved'
        REJECTED = 'REJECTED', 'Rejected'

    employee    = models.ForeignKey(User, on_delete=models.CASCADE, related_name='leave_requests')
    leave_type  = models.CharField(max_length=20, choices=LeaveType.choices)
    start_date  = models.DateField()
    end_date    = models.DateField()
    reason      = models.TextField()
    status      = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_leaves')
    created_at  = models.DateTimeField(auto_now_add=True)

    @property
    def total_days(self):
        return (self.end_date - self.start_date).days + 1

    def __str__(self):
        return f"{self.employee.get_full_name()} - {self.leave_type} ({self.total_days} days)"


class PayrollRecord(models.Model):
    class Status(models.TextChoices):
        DRAFT     = 'DRAFT',     'Draft'
        CONFIRMED = 'CONFIRMED', 'Confirmed'
        PAID      = 'PAID',      'Paid'

    employee        = models.ForeignKey(User, on_delete=models.CASCADE, related_name='payrolls')
    month           = models.PositiveIntegerField()   # 1-12
    year            = models.PositiveIntegerField()
    base_salary     = models.DecimalField(max_digits=10, decimal_places=2)
    overtime_hours  = models.DecimalField(max_digits=6, decimal_places=2, default=0)
    overtime_pay    = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    deductions      = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    bonus           = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    net_salary      = models.DecimalField(max_digits=10, decimal_places=2)
    status          = models.CharField(max_length=20, choices=Status.choices, default=Status.DRAFT)
    notes           = models.TextField(blank=True)
    created_at      = models.DateTimeField(auto_now_add=True)
    paid_at         = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ['employee', 'month', 'year']
        ordering        = ['-year', '-month']

    def __str__(self):
        return f"{self.employee.get_full_name()} - {self.month}/{self.year} ({self.status})"