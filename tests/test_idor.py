import pytest
from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from accounts.models import Branch
from tests.factories import TableFactory

User = get_user_model()


@pytest.fixture
def branch_b(db):
    return Branch.objects.create(name='Branch B', address='456 Other St', phone='+251911222333')


@pytest.fixture
def manager_b(db, branch_b):
    return User.objects.create_user(
        username='manager_b', password='x', role='MANAGER',
        branch=branch_b, email='mb@test.com'
    )


@pytest.fixture
def manager_b_client(manager_b):
    client = APIClient()
    client.force_authenticate(user=manager_b)
    return client


@pytest.mark.django_db
class TestCrossBranchIsolation:
    """A manager in Branch B must not reach Branch A's objects by id."""

    def test_cannot_read_other_branch_table(self, manager_b_client, branch):
        table = TableFactory(branch=branch)  # branch == "Test Branch" (branch A)
        res = manager_b_client.get(reverse('table-detail', kwargs={'pk': table.id}))
        assert res.status_code == 404

    def test_cannot_modify_other_branch_table(self, manager_b_client, branch):
        table = TableFactory(branch=branch, status='AVAILABLE')
        res = manager_b_client.patch(
            reverse('table-detail', kwargs={'pk': table.id}),
            {'status': 'OUT_OF_SERVICE'}
        )
        assert res.status_code == 404
        table.refresh_from_db()
        assert table.status == 'AVAILABLE'

    def test_cannot_read_other_branch_user(self, manager_b_client, waiter_user):
        # waiter_user belongs to branch A
        res = manager_b_client.get(reverse('user-detail', kwargs={'pk': waiter_user.id}))
        assert res.status_code == 404

    def test_admin_can_read_cross_branch_table(self, admin_client, branch_b):
        # admin (branch A) can reach a Branch B table — full system access
        table = TableFactory(branch=branch_b)
        res = admin_client.get(reverse('table-detail', kwargs={'pk': table.id}))
        assert res.status_code == 200
