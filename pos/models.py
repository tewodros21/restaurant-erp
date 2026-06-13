from django.db import models
from accounts.models import User, Branch
from tables.models import Table, TableSeat
from menu.models import MenuItem
from decimal import Decimal

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

    class Meta:
        indexes = [
            models.Index(fields=['branch', 'status']),
            models.Index(fields=['branch', '-created_at']),
        ]

    def __str__(self):
        return f"Order #{self.id} - Table {self.table} ({self.status})"

    @property
    def total_price(self):
        """Sum of every (non-cancelled) meal item's subtotal across all meals."""
        total = Decimal('0.00')
        for meal in self.meals.all():
            for item in meal.items.all():
                if item.status != MealItem.Status.CANCELLED:
                    total += item.subtotal
        return total

    # Alias kept for backwards compatibility with serializers/callers.
    @property
    def subtotal(self):
        return self.total_price


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

    meal       = models.ForeignKey(Meal, on_delete=models.CASCADE, related_name='items')
    # PROTECT: deleting a menu item must not silently destroy historical order
    # lines (and the bills derived from them). Callers should deactivate
    # (is_available=False) instead of deleting items that have been ordered.
    menu_item  = models.ForeignKey(MenuItem, on_delete=models.PROTECT)
    quantity   = models.PositiveIntegerField(default=1)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    item_type  = models.CharField(max_length=10, choices=ItemType.choices, default=ItemType.FOOD)
    status     = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    notes      = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        # Always ensure unit_price is Decimal
        if not self.unit_price:
            self.unit_price = Decimal(str(self.menu_item.price))
        super().save(*args, **kwargs)

    @property
    def subtotal(self):
        # Force both sides to correct types
        return Decimal(str(self.unit_price)) * int(self.quantity)

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

class Reservation(models.Model):
    class Status(models.TextChoices):
        PENDING   = 'PENDING',   'Pending'
        CONFIRMED = 'CONFIRMED', 'Confirmed'
        CHECKED_IN = 'CHECKED_IN', 'Checked In'
        CANCELLED = 'CANCELLED', 'Cancelled'
        NO_SHOW   = 'NO_SHOW',   'No Show'

    branch          = models.ForeignKey(Branch, on_delete=models.CASCADE, related_name='reservations')
    table           = models.ForeignKey(Table, on_delete=models.SET_NULL, null=True, related_name='reservations')
    customer_name   = models.CharField(max_length=100)
    customer_phone  = models.CharField(max_length=20)
    customer_email  = models.EmailField(blank=True)
    guest_count     = models.PositiveIntegerField()
    reservation_date = models.DateField()
    reservation_time = models.TimeField()
    status          = models.CharField(max_length=20, choices=Status.choices, default=Status.CONFIRMED)
    notes           = models.TextField(blank=True)
    created_by      = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_reservations')
    created_at      = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['reservation_date', 'reservation_time']
        indexes = [
            models.Index(fields=['branch', 'reservation_date', 'status']),
        ]

    def __str__(self):
        return f"{self.customer_name} - {self.reservation_date} {self.reservation_time}"


class Bill(models.Model):
    class Status(models.TextChoices):
        UNPAID = 'UNPAID', 'Unpaid'
        PAID   = 'PAID',   'Paid'
        VOIDED = 'VOIDED', 'Voided'

    order      = models.OneToOneField(Order, on_delete=models.CASCADE, related_name='bill')
    branch     = models.ForeignKey(Branch, on_delete=models.CASCADE, related_name='bills')
    status     = models.CharField(max_length=10, choices=Status.choices, default=Status.UNPAID)
    subtotal   = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    tax_rate   = models.DecimalField(max_digits=5, decimal_places=2, default=15.00)  # 15% VAT
    tax_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    discount   = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total      = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    notes      = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def calculate(self):
        cents = Decimal('0.01')
        # Field defaults (e.g. tax_rate=15.00) are plain floats until a DB
        # round-trip, so coerce everything to Decimal before arithmetic.
        tax_rate = Decimal(str(self.tax_rate))
        discount = Decimal(str(self.discount))
        self.subtotal   = self.order.total_price.quantize(cents)
        self.tax_amount = (self.subtotal * (tax_rate / Decimal('100'))).quantize(cents)
        self.total      = (self.subtotal + self.tax_amount - discount).quantize(cents)
        self.save()

    def __str__(self):
        return f"Bill #{self.id} - Order #{self.order.id} ({self.status})"


class BillItem(models.Model):
    bill       = models.ForeignKey(Bill, on_delete=models.CASCADE, related_name='items')
    meal_item  = models.ForeignKey(MealItem, on_delete=models.CASCADE)
    name       = models.CharField(max_length=100)
    quantity   = models.PositiveIntegerField()
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    subtotal   = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.quantity}x {self.name} = {self.subtotal}"


class Payment(models.Model):
    class Method(models.TextChoices):
        CASH           = 'CASH',           'Cash'
        BANK_TRANSFER  = 'BANK_TRANSFER',  'Bank Transfer'
        CREDIT_CARD    = 'CREDIT_CARD',    'Credit Card'
        TELEBIRR       = 'TELEBIRR',       'Telebirr'
        DIGITAL_WALLET = 'DIGITAL_WALLET', 'Digital Wallet'
        CHECK          = 'CHECK',          'Check'

    bill           = models.OneToOneField(Bill, on_delete=models.CASCADE, related_name='payment')
    method         = models.CharField(max_length=20, choices=Method.choices)
    amount_paid    = models.DecimalField(max_digits=10, decimal_places=2)
    change_given   = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    reference_code = models.CharField(max_length=100, blank=True)  # for transfers
    processed_by   = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    paid_at        = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Payment #{self.id} - {self.method} - {self.amount_paid}"


class Notification(models.Model):
    class Type(models.TextChoices):
        RESERVATION_CONFIRMED  = 'RESERVATION_CONFIRMED',  'Reservation Confirmed'
        RESERVATION_CANCELLED  = 'RESERVATION_CANCELLED',  'Reservation Cancelled'
        RESERVATION_REMINDER   = 'RESERVATION_REMINDER',   'Reservation Reminder'
        LOW_STOCK              = 'LOW_STOCK',              'Low Stock'
        ORDER_READY            = 'ORDER_READY',            'Order Ready'

    type        = models.CharField(max_length=30, choices=Type.choices)
    recipient   = models.CharField(max_length=100)   # phone or email
    message     = models.TextField()
    is_sent     = models.BooleanField(default=False)
    created_at  = models.DateTimeField(auto_now_add=True)
    sent_at     = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.type} → {self.recipient}"