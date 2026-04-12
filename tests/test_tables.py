import pytest
from django.urls import reverse
from tests.factories import TableFactory


@pytest.mark.django_db
class TestTableAPI:

    def test_get_available_tables(self, waiter_client, waiter_user):
        TableFactory.create_batch(3, branch=waiter_user.branch, status='AVAILABLE')
        TableFactory(branch=waiter_user.branch, status='OCCUPIED')

        url      = reverse('available-tables')
        response = waiter_client.get(url)
        assert response.status_code == 200
        # ✅ Fix — pagination wraps results
        assert response.data['count'] == 3
        assert len(response.data['results']) == 3

    def test_update_table_status(self, waiter_client, waiter_user):
        table = TableFactory(branch=waiter_user.branch, status='AVAILABLE')
        url   = reverse('update-table-status', kwargs={'pk': table.id})
        response = waiter_client.patch(url, {'status': 'OCCUPIED'})
        assert response.status_code == 200
        assert response.data['status'] == 'OCCUPIED'

    def test_invalid_status_rejected(self, waiter_client, waiter_user):
        table    = TableFactory(branch=waiter_user.branch)
        url      = reverse('update-table-status', kwargs={'pk': table.id})
        response = waiter_client.patch(url, {'status': 'FLYING'})
        assert response.status_code == 400