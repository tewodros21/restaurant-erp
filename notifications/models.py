from django.db import models
from accounts.models import User, Branch


class Notification(models.Model):
    class Type(models.TextChoices):
        LOW_STOCK       = 'LOW_STOCK',       'Low Stock Alert'
        EXPIRED_ITEM    = 'EXPIRED_ITEM',    'Expired Item Alert'
        RESERVATION     = 'RESERVATION',     'Reservation Reminder'
        MAINTENANCE     = 'MAINTENANCE',     'Maintenance Due'
        PAYROLL         = 'PAYROLL',         'Payroll Ready'
        ORDER           = 'ORDER',           'Order Update'
        GENERAL         = 'GENERAL',         'General'

    class Priority(models.TextChoices):
        LOW    = 'LOW',    'Low'
        MEDIUM = 'MEDIUM', 'Medium'
        HIGH   = 'HIGH',   'High'

    recipient   = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    branch      = models.ForeignKey(Branch, on_delete=models.CASCADE, related_name='notifications')
    type        = models.CharField(max_length=30, choices=Type.choices, default=Type.GENERAL)
    priority    = models.CharField(max_length=10, choices=Priority.choices, default=Priority.MEDIUM)
    title       = models.CharField(max_length=200)
    message     = models.TextField()
    is_read     = models.BooleanField(default=False)
    data        = models.JSONField(null=True, blank=True)  # extra context e.g. ingredient_id
    created_at  = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.type} → {self.recipient.get_full_name()} - {self.title}"