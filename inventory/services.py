from .models import Ingredient, RecipeIngredient, StockTransaction, WastageLog
from django.db import transaction


def deduct_stock_for_order(order):
    """
    Called when an order is submitted.
    Deducts ingredients from stock based on recipe.
    """
    with transaction.atomic():
        for meal in order.meals.all():
            for meal_item in meal.items.all():
                menu_item = meal_item.menu_item
                quantity  = meal_item.quantity

                # Check if menu item has a recipe
                try:
                    recipe = menu_item.recipe
                except Exception:
                    continue  # No recipe defined, skip

                # Deduct each ingredient
                for recipe_ingredient in recipe.ingredients.all():
                    ingredient      = recipe_ingredient.ingredient
                    deduct_quantity = recipe_ingredient.quantity * quantity

                    # Deduct from stock
                    ingredient.current_stock -= deduct_quantity
                    ingredient.save()

                    # Log the transaction
                    StockTransaction.objects.create(
                        ingredient       = ingredient,
                        transaction_type = 'OUT',
                        quantity         = deduct_quantity,
                        notes            = f"Auto-deducted for Order #{order.id}",
                        created_by       = order.waiter
                    )

                    # Check for low stock
                    if ingredient.is_low_stock:
                        send_low_stock_alert(ingredient)

                    # Check for expiry
                    if ingredient.is_expired:
                        log_expired_ingredient(ingredient, order.waiter)


def send_low_stock_alert(ingredient):
    """Send alert to manager when stock is low"""
    from notifications.services import send_low_stock_alert as notify
    notify(ingredient)


def log_expired_ingredient(ingredient, user):
    """Log expired ingredient as wastage"""
    from notifications.services import send_expired_alert as notify
    notify(ingredient)

    WastageLog.objects.create(
        branch     = ingredient.branch,
        ingredient = ingredient,
        quantity   = ingredient.current_stock,
        reason     = "Expired product auto-detected",
        logged_by  = user
    )


def add_stock(ingredient, quantity, user, notes=''):
    """Add stock (when new stock arrives)"""
    with transaction.atomic():
        ingredient.current_stock += quantity
        ingredient.save()

        StockTransaction.objects.create(
            ingredient       = ingredient,
            transaction_type = 'IN',
            quantity         = quantity,
            notes            = notes or f"Stock added by {user.get_full_name()}",
            created_by       = user
        )