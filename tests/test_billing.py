import pytest
from decimal import Decimal
from django.urls import reverse
from tests.factories import TableFactory, MenuFactory, MenuSectionFactory, MenuItemFactory


def _order_with_items(client, branch, price='100.00', qty=2):
    """Create + populate + submit an order, returning its id."""
    table = TableFactory(branch=branch)
    order_id = client.post(reverse('create-order'), {
        'table': table.id, 'order_type': 'DINE_IN'
    }).data['id']

    meal_id = client.post(
        reverse('add-meal', kwargs={'order_id': order_id}),
        {'seat_label': 'Seat 1'}
    ).data['id']

    menu = MenuFactory(branch=branch)
    section = MenuSectionFactory(menu=menu)
    item = MenuItemFactory(section=section, category='FOOD', price=price)
    client.post(
        reverse('add-meal-item', kwargs={'meal_id': meal_id}),
        {'menu_item_id': item.id, 'quantity': qty}
    )
    return order_id


@pytest.mark.django_db
class TestBilling:
    """Covers the billing/payment path that was previously unrouted and broken."""

    def test_order_total_price_sums_line_items(self, admin_client, admin_user):
        order_id = _order_with_items(admin_client, admin_user.branch, price='100.00', qty=2)
        from pos.models import Order
        order = Order.objects.get(id=order_id)
        # 2 × 100.00 = 200.00 (the old Order.subtotal referenced non-existent fields)
        assert order.total_price == Decimal('200.00')

    def test_generate_bill_computes_tax_and_total(self, admin_client, admin_user):
        order_id = _order_with_items(admin_client, admin_user.branch, price='100.00', qty=2)
        admin_client.post(reverse('submit-order', kwargs={'order_id': order_id}))

        res = admin_client.post(reverse('generate-bill', kwargs={'order_id': order_id}))
        assert res.status_code == 201
        # subtotal 200.00, default VAT 15% → tax 30.00, total 230.00
        assert Decimal(str(res.data['subtotal'])) == Decimal('200.00')
        assert Decimal(str(res.data['tax_amount'])) == Decimal('30.00')
        assert Decimal(str(res.data['total'])) == Decimal('230.00')

    def test_cannot_generate_bill_twice(self, admin_client, admin_user):
        order_id = _order_with_items(admin_client, admin_user.branch)
        admin_client.post(reverse('submit-order', kwargs={'order_id': order_id}))
        admin_client.post(reverse('generate-bill', kwargs={'order_id': order_id}))
        res = admin_client.post(reverse('generate-bill', kwargs={'order_id': order_id}))
        assert res.status_code == 400

    def test_process_payment_marks_paid_and_returns_change(self, admin_client, admin_user):
        order_id = _order_with_items(admin_client, admin_user.branch, price='100.00', qty=2)
        admin_client.post(reverse('submit-order', kwargs={'order_id': order_id}))
        bill = admin_client.post(reverse('generate-bill', kwargs={'order_id': order_id})).data
        bill_id = bill['id']

        res = admin_client.post(
            reverse('process-payment', kwargs={'bill_id': bill_id}),
            {'method': 'CASH', 'amount_paid': '250.00'}
        )
        assert res.status_code == 200
        # 250.00 paid on a 230.00 total → 20.00 change, no float drift
        assert Decimal(str(res.data['change'])) == Decimal('20.00')
        assert res.data['bill']['status'] == 'PAID'

    def test_payment_rejects_insufficient_amount(self, admin_client, admin_user):
        order_id = _order_with_items(admin_client, admin_user.branch, price='100.00', qty=2)
        admin_client.post(reverse('submit-order', kwargs={'order_id': order_id}))
        bill_id = admin_client.post(reverse('generate-bill', kwargs={'order_id': order_id})).data['id']

        res = admin_client.post(
            reverse('process-payment', kwargs={'bill_id': bill_id}),
            {'method': 'CASH', 'amount_paid': '10.00'}
        )
        assert res.status_code == 400


@pytest.mark.django_db
class TestPrivilegeEscalation:
    """A manager must not be able to promote a user to ADMIN (was possible before)."""

    def test_manager_cannot_change_role(self, manager_client, waiter_user):
        url = reverse('user-detail', kwargs={'pk': waiter_user.id})
        res = manager_client.patch(url, {'role': 'ADMIN'})
        assert res.status_code == 400
        waiter_user.refresh_from_db()
        assert waiter_user.role == 'WAITER'

    def test_admin_can_change_role(self, admin_client, waiter_user):
        url = reverse('user-detail', kwargs={'pk': waiter_user.id})
        res = admin_client.patch(url, {'role': 'CASHIER'})
        assert res.status_code == 200
        waiter_user.refresh_from_db()
        assert waiter_user.role == 'CASHIER'
