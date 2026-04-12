import pytest
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model

User = get_user_model()


@pytest.fixture
def api_client():
    """Base API client — no auth"""
    return APIClient()


@pytest.fixture
def branch(db):
    """Create a test branch"""
    from accounts.models import Branch
    return Branch.objects.create(
        name    = 'Test Branch',
        address = '123 Test Street',
        phone   = '+251911000000'
    )


@pytest.fixture
def admin_user(db, branch):
    """Create an admin user"""
    return User.objects.create_user(
        username = 'admin',
        password = 'testpass123',
        role     = 'ADMIN',
        branch   = branch,
        email    = 'admin@test.com'
    )


@pytest.fixture
def manager_user(db, branch):
    """Create a manager user"""
    return User.objects.create_user(
        username = 'manager',
        password = 'testpass123',
        role     = 'MANAGER',
        branch   = branch,
        email    = 'manager@test.com'
    )


@pytest.fixture
def waiter_user(db, branch):
    """Create a waiter user"""
    return User.objects.create_user(
        username = 'waiter',
        password = 'testpass123',
        role     = 'WAITER',
        branch   = branch,
        email    = 'waiter@test.com'
    )


@pytest.fixture
def chef_user(db, branch):
    """Create a chef user"""
    return User.objects.create_user(
        username = 'chef',
        password = 'testpass123',
        role     = 'CHEF',
        branch   = branch,
        email    = 'chef@test.com'
    )


@pytest.fixture
def admin_client(api_client, admin_user):
    """API client authenticated as admin"""
    api_client.force_authenticate(user=admin_user)
    return api_client


@pytest.fixture
def manager_client(api_client, manager_user):
    """API client authenticated as manager"""
    api_client.force_authenticate(user=manager_user)
    return api_client


@pytest.fixture
def waiter_client(api_client, waiter_user):
    """API client authenticated as waiter"""
    api_client.force_authenticate(user=waiter_user)
    return api_client


@pytest.fixture
def chef_client(api_client, chef_user):
    """API client authenticated as chef"""
    api_client.force_authenticate(user=chef_user)
    return api_client