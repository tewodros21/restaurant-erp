import pytest
from decimal import Decimal
from datetime import date, datetime, timedelta
from django.utils import timezone


# ─── Payroll money math ───────────────────────────────────────────────

@pytest.mark.django_db
class TestPayrollMath:
    def _profile(self, user, salary='6000', ot_rate='1.5'):
        from hr.models import EmployeeProfile, Department
        dept = Department.objects.create(branch=user.branch, name='Service')
        return EmployeeProfile.objects.create(
            user=user, department=dept, date_joined='2024-01-01',
            base_salary=Decimal(salary), overtime_rate=Decimal(ot_rate),
            contract_type='FULL_TIME',
        )

    def test_net_salary_includes_overtime_and_absence(self, waiter_user):
        from hr.models import AttendanceRecord
        from hr.services import generate_payroll
        self._profile(waiter_user, salary='6000', ot_rate='1.5')

        # One 10h day (2h overtime) and one absent day in Jan 2026.
        AttendanceRecord.objects.create(
            employee=waiter_user, date=date(2026, 1, 6),
            clock_in=timezone.make_aware(datetime(2026, 1, 6, 8, 0)),
            clock_out=timezone.make_aware(datetime(2026, 1, 6, 18, 0)),
            status='PRESENT',
        )
        AttendanceRecord.objects.create(
            employee=waiter_user, date=date(2026, 1, 7), status='ABSENT',
        )

        payroll, _ = generate_payroll(waiter_user, month=1, year=2026)
        # base 6000; daily=200; hourly=25; ot=2*25*1.5=75; deduction=1*200=200
        assert payroll.overtime_pay == Decimal('75.00')
        assert payroll.deductions == Decimal('200.00')
        assert payroll.net_salary == Decimal('5875.00')  # 6000 + 75 - 200

    def test_unpaid_leave_is_deducted(self, waiter_user):
        from hr.models import LeaveRequest
        from hr.services import generate_payroll
        self._profile(waiter_user, salary='6000')

        LeaveRequest.objects.create(
            employee=waiter_user, leave_type='UNPAID',
            start_date=date(2026, 1, 10), end_date=date(2026, 1, 12),  # 3 days
            reason='x', status='APPROVED',
        )
        payroll, _ = generate_payroll(waiter_user, month=1, year=2026)
        # daily=200; 3 unpaid days => 600 deduction
        assert payroll.deductions == Decimal('600.00')
        assert payroll.net_salary == Decimal('5400.00')

    def test_bonus_is_added_to_net(self, waiter_user):
        from hr.services import generate_payroll
        self._profile(waiter_user, salary='6000')
        payroll, _ = generate_payroll(waiter_user, month=2, year=2026, bonus='500')
        assert payroll.bonus == Decimal('500.00')
        assert payroll.net_salary == Decimal('6500.00')


# ─── Asset depreciation ───────────────────────────────────────────────

@pytest.mark.django_db
class TestDepreciation:
    def _asset(self, branch, method, price='12000', salvage='0', life=5, value=None):
        from assets.models import Asset
        return Asset.objects.create(
            branch=branch, name='Oven', purchase_date='2026-01-01',
            purchase_price=Decimal(price), salvage_value=Decimal(salvage),
            current_value=Decimal(value if value is not None else price),
            useful_life_years=life, depreciation_method=method, status='ACTIVE',
        )

    def test_straight_line_monthly(self, branch):
        asset = self._asset(branch, 'STRAIGHT_LINE', price='12000', life=5)
        # annual = 12000/5 = 2400; monthly = 200
        assert asset.monthly_depreciation == Decimal('200.00')

    def test_declining_balance_is_nonzero_and_shrinks(self, branch):
        asset = self._asset(branch, 'DECLINING_BALANCE', price='12000', life=5)
        # rate = 2/5 = 0.4; annual = 12000*0.4 = 4800; monthly = 400
        first = asset.monthly_depreciation
        assert first == Decimal('400.00')
        # After book value drops, monthly depreciation should shrink.
        asset.current_value = Decimal('6000')
        assert asset.monthly_depreciation == Decimal('200.00')

    def test_record_amount_matches_value_drop_at_salvage_floor(self, branch):
        from assets.services import apply_monthly_depreciation
        # Almost fully depreciated: only 50 above salvage, monthly would be 200.
        asset = self._asset(branch, 'STRAIGHT_LINE', price='12000', salvage='1000',
                            life=5, value='1050')
        record, _ = apply_monthly_depreciation(asset)
        assert record is not None
        asset.refresh_from_db()
        assert asset.current_value == Decimal('1000.00')  # clamped to salvage
        # depreciation_amount must equal the actual drop (50), not the raw 200
        assert record.depreciation_amount == record.value_before - record.value_after
        assert record.depreciation_amount == Decimal('50.00')


# ─── Inventory expired-wastage idempotency ────────────────────────────

@pytest.mark.django_db
class TestExpiredWastage:
    def test_expired_logged_once_and_stock_zeroed(self, branch, waiter_user):
        from inventory.models import WastageLog, Ingredient
        from inventory.services import log_expired_ingredient
        ing = Ingredient.objects.create(
            branch=branch, name='Milk', current_stock=Decimal('20'),
            minimum_stock=Decimal('5'), cost_per_unit=Decimal('2'),
            expiration_date=date.today() - timedelta(days=1),
        )
        log_expired_ingredient(ing, waiter_user)
        log_expired_ingredient(ing, waiter_user)  # second call must be a no-op

        ing.refresh_from_db()
        assert ing.current_stock == Decimal('0')
        assert WastageLog.objects.filter(ingredient=ing).count() == 1


# ─── Menu item delete is protected when it has order history ──────────

@pytest.mark.django_db
class TestProtectedMenuDelete:
    def test_delete_ordered_item_returns_409(self, admin_client, admin_user):
        from django.urls import reverse
        from tests.factories import MenuFactory, MenuSectionFactory, MenuItemFactory, TableFactory
        menu = MenuFactory(branch=admin_user.branch)
        section = MenuSectionFactory(menu=menu)
        item = MenuItemFactory(section=section, category='FOOD', price='100.00')

        # Order the item so a MealItem references it.
        order_id = admin_client.post(reverse('create-order'), {
            'table': TableFactory(branch=admin_user.branch).id, 'order_type': 'DINE_IN'
        }).data['id']
        meal_id = admin_client.post(
            reverse('add-meal', kwargs={'order_id': order_id}), {'seat_label': 'S1'}
        ).data['id']
        admin_client.post(
            reverse('add-meal-item', kwargs={'meal_id': meal_id}),
            {'menu_item_id': item.id, 'quantity': 1}
        )

        res = admin_client.delete(reverse('item-detail', kwargs={'pk': item.id}))
        assert res.status_code == 409

    def test_delete_section_with_ordered_item_returns_409(self, admin_client, admin_user):
        from django.urls import reverse
        from tests.factories import MenuFactory, MenuSectionFactory, MenuItemFactory, TableFactory
        menu = MenuFactory(branch=admin_user.branch)
        section = MenuSectionFactory(menu=menu)
        item = MenuItemFactory(section=section, category='FOOD', price='100.00')

        order_id = admin_client.post(reverse('create-order'), {
            'table': TableFactory(branch=admin_user.branch).id, 'order_type': 'DINE_IN'
        }).data['id']
        meal_id = admin_client.post(
            reverse('add-meal', kwargs={'order_id': order_id}), {'seat_label': 'S1'}
        ).data['id']
        admin_client.post(
            reverse('add-meal-item', kwargs={'meal_id': meal_id}),
            {'menu_item_id': item.id, 'quantity': 1}
        )

        # Cascading the section delete hits the PROTECT-ed item -> clean 409, not 500
        res = admin_client.delete(reverse('section-detail', kwargs={'pk': section.id}))
        assert res.status_code == 409
