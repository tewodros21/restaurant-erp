import pytest
from django.urls import reverse
from accounts.models import Branch


@pytest.mark.django_db
class TestBranchAPI:

    def test_admin_can_create_branch(self, admin_client):
        url  = reverse('branch-list')
        data = {
            'name':    'New Branch',
            'address': '456 Test Ave',
            'phone':   '+251911111111'
        }
        response = admin_client.post(url, data)
        assert response.status_code == 201
        assert response.data['name'] == 'New Branch'

    def test_manager_cannot_create_branch(self, manager_client):
        url      = reverse('branch-list')
        response = manager_client.post(url, {'name': 'Hack Branch'})
        assert response.status_code == 403  # forbidden

    def test_unauthenticated_cannot_access(self, api_client):
        url      = reverse('branch-list')
        response = api_client.get(url)
        assert response.status_code == 401  # unauthorized


@pytest.mark.django_db
class TestUserRegistration:

    def test_admin_can_register_user(self, admin_client, branch):
        url  = reverse('register')
        data = {
            'username':   'newwaiter',
            'password':   'testpass123',
            'email':      'waiter2@test.com',
            'first_name': 'John',
            'last_name':  'Doe',
            'role':       'WAITER',
            'branch':     branch.id
        }
        response = admin_client.post(url, data)
        assert response.status_code == 201

    def test_waiter_cannot_register_user(self, waiter_client, branch):
        url      = reverse('register')
        response = waiter_client.post(url, {'username': 'hacker'})
        assert response.status_code == 403


@pytest.mark.django_db
class TestJWTAuth:

    def test_obtain_token(self, api_client, admin_user):
        url      = reverse('token-obtain')
        response = api_client.post(url, {
            'username': 'admin',
            'password': 'testpass123'
        })
        assert response.status_code == 200
        assert 'access' in response.data
        assert 'refresh' in response.data

    def test_wrong_password_rejected(self, api_client, admin_user):
        url      = reverse('token-obtain')
        response = api_client.post(url, {
            'username': 'admin',
            'password': 'wrongpassword'
        })
        assert response.status_code == 401