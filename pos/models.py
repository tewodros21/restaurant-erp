from django.db import models
from accounts.models import User, Branch
from tables.models import Table, TableSeat
from menu.models import MenuItem


class Order(models.Model):
    class Status(models.TextChoices):
        PENDING   = 'PENDING',   'Pending'
        CONFIRMED = 'CONFIRMED', 'Confirmed'
        PREPARING = 'PREPARING', 'Preparing'
        READY     = 'READY',     'Ready'
        SERVED    = 'SERVED',    'Served'
        CANCELLED = 'CANCELLED', 'Cancelled'
        COMPLETED = 'COMPLETED', 'Completed'

    class OrderType(models.TextChoices):
        DINE_IN  = 'DINE_IN',  'Dine In'
        TAKEAWAY = 'TAKEAWAY', 'Takeaway'
        DELIVERY = 'DELIVERY', 'Delivery'

    branch       = models.ForeignKey(Branch, on_delete=models.CASCADE, related_name='orders')
    table        = models.ForeignKey(Table, on_delete=models.SET_NULL, null=True, blank=True, related_name='orders')
    waiter       = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='waiter_orders')
    chef         = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='chef_orders')
    order_type   = models.CharField(max_length=20, choices=OrderType.choices, default=OrderType.DINE_IN)
    status       = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    notes        = models.TextField(blank=True)
    created_at   = models.DateTimeField(auto_now_add=True)
    updated_at   = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Order #{self.id} - Table {self.table} ({self.status})"

    @property
    def total_price(self):
        return sum(item.subtotal for meal in self.meals.all() for item in meal.items.all())


class Meal(models.Model):
    """Represents the meal for one seat at a table"""
    order      = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='meals')
    seat       = models.ForeignKey(TableSeat, on_delete=models.SET_NULL, null=True, blank=True)
    seat_label = models.CharField(max_length=20, default='Seat 1')  # fallback label
    notes      = models.TextField(blank=True)

    def __str__(self):
        return f"Meal - Order #{self.order.id} - {self.seat_label}"


class MealItem(models.Model):
    class Status(models.TextChoices):
        PENDING   = 'PENDING',   'Pending'
        PREPARING = 'PREPARING', 'Preparing'
        READY     = 'READY',     'Ready'
        SERVED    = 'SERVED',    'Served'
        CANCELLED = 'CANCELLED', 'Cancelled'

    class ItemType(models.TextChoices):
        FOOD  = 'FOOD',  'Food'
        DRINK = 'DRINK', 'Drink'

    meal        = models.ForeignKey(Meal, on_delete=models.CASCADE, related_name='items')
    menu_item   = models.ForeignKey(MenuItem, on_delete=models.CASCADE)
    quantity    = models.PositiveIntegerField(default=1)
    unit_price  = models.DecimalField(max_digits=10, decimal_places=2)
    item_type   = models.CharField(max_length=10, choices=ItemType.choices, default=ItemType.FOOD)
    status      = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    notes       = models.TextField(blank=True)  # e.g. "no onions"
    created_at  = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        # Auto-set unit price from menu item on creation
        if not self.unit_price:
            self.unit_price = self.menu_item.price
        super().save(*args, **kwargs)

    @property
    def subtotal(self):
        return self.unit_price * self.quantity

    def __str__(self):
        return f"{self.quantity}x {self.menu_item.name} ({self.status})"


class KOT(models.Model):
    """Kitchen Order Ticket"""
    order      = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='kots')
    items      = models.ManyToManyField(MealItem, related_name='kot')
    printed    = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"KOT #{self.id} - Order #{self.order.id}"


class BOT(models.Model):
    """Bar Order Ticket"""
    order      = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='bots')
    items      = models.ManyToManyField(MealItem, related_name='bot')
    printed    = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"BOT #{self.id} - Order #{self.order.id}"