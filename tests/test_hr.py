import pytest
from hr.services import clock_in, clock_out, generate_payroll
from tests.factories import UserFactory


@pytest.mark.django_db
class TestAttendance:

    def test_clock_in(self, waiter_user):
        record, message = clock_in(waiter_user)
        assert record is not None
        assert message == 'Clocked in successfully'
        assert record.clock_in is not None

    def test_cannot_clock_in_twice(self, waiter_user):
        clock_in(waiter_user)
        record, message = clock_in(waiter_user)
        assert record is None
        assert 'Already clocked in' in message

    def test_clock_out(self, waiter_user):
        from django.utils import timezone
        from datetime import timedelta
        from hr.models import AttendanceRecord

        # Manually create clock-in 9 hours ago
        now = timezone.now()
        AttendanceRecord.objects.create(
            employee  = waiter_user,
            date      = now.date(),
            clock_in  = now - timedelta(hours=9),
            status    = AttendanceRecord.Status.PRESENT
        )

        record, message = clock_out(waiter_user)
        assert record is not None
        assert record.clock_out is not None
        assert record.hours_worked > 0

    def test_hours_worked_calculation(self, waiter_user):
        from django.utils import timezone
        from datetime import timedelta
        from hr.models import AttendanceRecord

        now = timezone.now()
        record = AttendanceRecord.objects.create(
            employee  = waiter_user,
            date      = now.date(),
            clock_in  = now - timedelta(hours=9),
            clock_out = now,
            status    = 'PRESENT'
        )
        assert record.hours_worked == 9.0
        assert record.overtime_hours == 1.0  # 9 - 8 standard hours


@pytest.mark.django_db
class TestPayroll:

    def test_generate_payroll(self, waiter_user):
        from hr.models import EmployeeProfile, Department
        from tests.factories import BranchFactory

        dept = Department.objects.create(
            branch = waiter_user.branch,
            name   = 'Service'
        )
        EmployeeProfile.objects.create(
            user          = waiter_user,
            department    = dept,
            date_joined   = '2024-01-01',
            base_salary   = 5000,
            contract_type = 'FULL_TIME'
        )

        payroll, message = generate_payroll(waiter_user, month=1, year=2026)
        assert payroll is not None
        assert payroll.base_salary == 5000
        assert payroll.status == 'DRAFT'