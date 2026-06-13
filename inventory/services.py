from .models import Ingredient, RecipeIngredient, StockTransaction, WastageLog
from django.db import transaction
from django.utils import timezone


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
                    deduct_quantity = recipe_ingredient.quantity * quantity

                    # Lock the ingredient row so concurrent orders can't lose
                    # updates via read-modify-write races.
                    ingredient = Ingredient.objects.select_for_update().get(
                        pk=recipe_ingredient.ingredient_id
                    )
                    ingredient.current_stock -= deduct_quantity
                    ingredient.save(update_fields=['current_stock', 'updated_at'])

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


EXPIRED_WASTAGE_REASON = "Expired product auto-detected"


def log_expired_ingredient(ingredient, user):
    """Log an expired ingredient as wastage — once — and remove it from stock.

    Previously this re-logged the full current_stock as wastage on *every*
    order that touched the ingredient and never zeroed the stock, producing
    duplicate wastage rows. Now it is idempotent per ingredient per day and
    actually writes off the expired stock.
    """
    if ingredient.current_stock <= 0:
        return  # nothing left to write off

    today = timezone.localdate()
    already_logged = WastageLog.objects.filter(
        ingredient = ingredient,
        reason     = EXPIRED_WASTAGE_REASON,
        created_at__date = today,
    ).exists()
    if already_logged:
        return

    from notifications.services import send_expired_alert as notify
    notify(ingredient)

    wasted = ingredient.current_stock
    WastageLog.objects.create(
        branch     = ingredient.branch,
        ingredient = ingredient,
        quantity   = wasted,
        reason     = EXPIRED_WASTAGE_REASON,
        logged_by  = user
    )
    StockTransaction.objects.create(
        ingredient       = ingredient,
        transaction_type = 'WASTAGE',
        quantity         = wasted,
        notes            = EXPIRED_WASTAGE_REASON,
        created_by       = user,
    )
    # Write off the expired stock so it isn't counted or re-logged.
    ingredient.current_stock = 0
    ingredient.save(update_fields=['current_stock', 'updated_at'])


def add_stock(ingredient, quantity, user, notes=''):
    """Add stock (when new stock arrives)"""
    with transaction.atomic():
        # Lock the row so concurrent stock-ins don't lose updates.
        ingredient = Ingredient.objects.select_for_update().get(pk=ingredient.pk)
        ingredient.current_stock += quantity
        ingredient.save(update_fields=['current_stock', 'updated_at'])

        StockTransaction.objects.create(
            ingredient       = ingredient,
            transaction_type = 'IN',
            quantity         = quantity,
            notes            = notes or f"Stock added by {user.get_full_name()}",
            created_by       = user
        )