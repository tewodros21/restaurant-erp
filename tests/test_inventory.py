import pytest
from tests.factories import IngredientFactory, MenuItemFactory, MenuSectionFactory, MenuFactory
from inventory.models import Recipe, RecipeIngredient, StockTransaction


@pytest.mark.django_db
class TestInventoryModels:

    def test_ingredient_is_low_stock(self, branch):
        ingredient = IngredientFactory(
            branch        = branch,
            current_stock = 5,
            minimum_stock = 10
        )
        assert ingredient.is_low_stock == True

    def test_ingredient_not_low_stock(self, branch):
        ingredient = IngredientFactory(
            branch        = branch,
            current_stock = 50,
            minimum_stock = 10
        )
        assert ingredient.is_low_stock == False

    def test_expired_ingredient(self, branch):
        from datetime import date, timedelta
        ingredient = IngredientFactory(
            branch          = branch,
            expiration_date = date.today() - timedelta(days=1)
        )
        assert ingredient.is_expired == True

    def test_not_expired_ingredient(self, branch):
        from datetime import date, timedelta
        ingredient = IngredientFactory(
            branch          = branch,
            expiration_date = date.today() + timedelta(days=10)
        )
        assert ingredient.is_expired == False


@pytest.mark.django_db
class TestAutoDeduction:

    def test_stock_deducted_on_order_submit(self, waiter_client, waiter_user):
        from inventory.services import deduct_stock_for_order
        from tests.factories import OrderFactory, TableFactory
        from pos.models import Meal, MealItem

        # Setup ingredient and recipe
        ingredient = IngredientFactory(branch=waiter_user.branch, current_stock=100)
        menu       = MenuFactory(branch=waiter_user.branch)
        section    = MenuSectionFactory(menu=menu)
        menu_item  = MenuItemFactory(section=section)
        recipe     = Recipe.objects.create(menu_item=menu_item)
        RecipeIngredient.objects.create(
            recipe     = recipe,
            ingredient = ingredient,
            quantity   = 10  # uses 10 units per order
        )

        # Create order with meal item
        table = TableFactory(branch=waiter_user.branch)
        order = OrderFactory(branch=waiter_user.branch, waiter=waiter_user, table=table)
        meal  = Meal.objects.create(order=order, seat_label='Seat 1')
        MealItem.objects.create(
            meal       = meal,
            menu_item  = menu_item,
            quantity   = 2,         # order 2 → should deduct 20 units
            unit_price = menu_item.price,
            item_type  = 'FOOD'
        )

        # Run deduction
        deduct_stock_for_order(order)

        ingredient.refresh_from_db()
        assert ingredient.current_stock == 80  # 100 - (10 * 2)