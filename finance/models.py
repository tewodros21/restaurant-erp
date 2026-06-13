from django.db import models
from accounts.models import Branch, User


class ExpenseCategory(models.Model):
    name        = models.CharField(max_length=100)  # e.g. Rent, Utilities, Procurement
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['name']


class Expense(models.Model):
    class Status(models.TextChoices):
        PENDING  = 'PENDING',  'Pending'
        APPROVED = 'APPROVED', 'Approved'
        REJECTED = 'REJECTED', 'Rejected'

    branch      = models.ForeignKey(Branch, on_delete=models.CASCADE, related_name='expenses')
    category    = models.ForeignKey(ExpenseCategory, on_delete=models.SET_NULL, null=True)
    title       = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    amount      = models.DecimalField(max_digits=12, decimal_places=2)
    date        = models.DateField()
    status      = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    approved_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='approved_expenses'
    )
    receipt     = models.ImageField(upload_to='expense_receipts/', null=True, blank=True)
    created_by  = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='expenses_created')
    created_at  = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.title} - {self.amount} ({self.date})"

    class Meta:
        ordering = ['-date']
        indexes = [
            models.Index(fields=['branch', 'date', 'status']),
        ]


class DailyReport(models.Model):
    """Auto-generated daily summary"""
    branch              = models.ForeignKey(Branch, on_delete=models.CASCADE, related_name='daily_reports')
    date                = models.DateField()
    total_sales         = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_orders        = models.PositiveIntegerField(default=0)
    total_expenses      = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    cash_sales          = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    card_sales          = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    transfer_sales      = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    digital_wallet_sales = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    net_profit          = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    created_at          = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['branch', 'date']
        ordering        = ['-date']

    def __str__(self):
        return f"{self.branch.name} - {self.date} - Sales: {self.total_sales}"