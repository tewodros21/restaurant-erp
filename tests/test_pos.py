import pytest
from django.urls import reverse
from tests.factories import TableFactory, MenuItemFactory, MenuSectionFactory, MenuFactory


@pytest.mark.django_db
class TestOrderFlow:
    """Tests the complete order lifecycle"""

    def test_waiter_can_create_order(self, waiter_client, waiter_user):
        table    = TableFactory(branch=waiter_user.branch, status='AVAILABLE')
        url      = reverse('create-order')
        response = waiter_client.post(url, {
            'table':      table.id,
            'order_type': 'DINE_IN'
        })
        assert response.status_code == 201
        assert response.data['status'] == 'PENDING'

    def test_create_order_marks_table_occupied(self, waiter_client, waiter_user):
        from tables.models import Table
        table = TableFactory(branch=waiter_user.branch, status='AVAILABLE')
        waiter_client.post(reverse('create-order'), {
            'table':      table.id,
            'order_type': 'DINE_IN'
        })
        table.refresh_from_db()
        assert table.status == 'OCCUPIED'

    def test_full_order_flow(self, waiter_client, waiter_user):
        """
        Full flow:
        Create order → add meal → add item → submit
        → check KOT generated
        """
        # 1. Create order
        table    = TableFactory(branch=waiter_user.branch)
        response = waiter_client.post(reverse('create-order'), {
            'table':      table.id,
            'order_type': 'DINE_IN'
        })
        order_id = response.data['id']
        assert response.status_code == 201

        # 2. Add meal for seat 1
        response = waiter_client.post(
            reverse('add-meal', kwargs={'order_id': order_id}),
            {'seat_label': 'Seat 1'}
        )
        meal_id = response.data['id']
        assert response.status_code == 201

        # 3. Add food item to meal
        menu    = MenuFactory(branch=waiter_user.branch)
        section = MenuSectionFactory(menu=menu)
        item    = MenuItemFactory(section=section, category='FOOD', price='100.00')

        response = waiter_client.post(
            reverse('add-meal-item', kwargs={'meal_id': meal_id}),
            {'menu_item_id': item.id, 'quantity': 2}
        )
        assert response.status_code == 201

        # 4. Submit order
        response = waiter_client.post(
            reverse('submit-order', kwargs={'order_id': order_id})
        )
        assert response.status_code == 200
        assert response.data['kot_generated'] == True
        assert response.data['order']['status'] == 'CONFIRMED'

    def test_cannot_submit_order_twice(self, waiter_client, waiter_user):
        table = TableFactory(branch=waiter_user.branch)
        res   = waiter_client.post(reverse('create-order'), {
            'table': table.id, 'order_type': 'DINE_IN'
        })
        order_id = res.data['id']

        # Submit once
        waiter_client.post(reverse('submit-order', kwargs={'order_id': order_id}))
        # Submit again — should fail
        response = waiter_client.post(
            reverse('submit-order', kwargs={'order_id': order_id})
        )
        assert response.status_code == 400