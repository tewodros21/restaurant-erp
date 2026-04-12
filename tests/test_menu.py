import pytest
from django.urls import reverse
from tests.factories import MenuFactory, MenuSectionFactory, MenuItemFactory


@pytest.mark.django_db
class TestMenuAPI:

    def test_manager_can_create_menu_item(self, manager_client, manager_user):
        menu    = MenuFactory(branch=manager_user.branch)
        section = MenuSectionFactory(menu=menu)
        url     = reverse('item-list')
        data    = {
            'section':          section.id,
            'name':             'Grilled Chicken',
            'price':            '150.00',
            'category':         'FOOD',
            'is_available':     True,
            'preparation_time': 20
        }
        response = manager_client.post(url, data)
        assert response.status_code == 201
        assert response.data['name'] == 'Grilled Chicken'

    def test_waiter_cannot_create_menu_item(self, waiter_client):
        url      = reverse('item-list')
        response = waiter_client.post(url, {'name': 'Hack Item'})
        assert response.status_code == 403

    def test_public_menu_accessible_without_auth(self, api_client, branch):
        menu = MenuFactory(branch=branch)
        url  = reverse('public-menu', kwargs={'branch_id': branch.id})
        response = api_client.get(url)
        assert response.status_code == 200