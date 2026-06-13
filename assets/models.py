from django.db import models
from accounts.models import Branch, User
from decimal import Decimal
import qrcode
from io import BytesIO
from django.core.files import File


class AssetCategory(models.Model):
    name        = models.CharField(max_length=100)  # e.g. Furniture, Electronics, Machinery
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['name']


class Asset(models.Model):
    class Status(models.TextChoices):
        ACTIVE      = 'ACTIVE',      'Active'
        MAINTENANCE = 'MAINTENANCE', 'Under Maintenance'
        RETIRED     = 'RETIRED',     'Retired'
        DISPOSED    = 'DISPOSED',    'Disposed'

    class DepreciationMethod(models.TextChoices):
        STRAIGHT_LINE    = 'STRAIGHT_LINE',    'Straight Line'
        DECLINING_BALANCE = 'DECLINING_BALANCE', 'Declining Balance'

    branch               = models.ForeignKey(Branch, on_delete=models.CASCADE, related_name='assets')
    category             = models.ForeignKey(AssetCategory, on_delete=models.SET_NULL, null=True)
    name                 = models.CharField(max_length=100)
    description          = models.TextField(blank=True)
    serial_number        = models.CharField(max_length=100, blank=True, unique=True, null=True)
    purchase_date        = models.DateField()
    purchase_price       = models.DecimalField(max_digits=12, decimal_places=2)
    current_value        = models.DecimalField(max_digits=12, decimal_places=2)
    salvage_value        = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    useful_life_years    = models.PositiveIntegerField(default=5)
    depreciation_method  = models.CharField(
        max_length=30,
        choices=DepreciationMethod.choices,
        default=DepreciationMethod.STRAIGHT_LINE
    )
    status               = models.CharField(max_length=20, choices=Status.choices, default=Status.ACTIVE)
    location             = models.CharField(max_length=100, blank=True)  # e.g. "Main Hall", "Kitchen"
    qr_code              = models.ImageField(upload_to='asset_qrcodes/', null=True, blank=True)
    assigned_to          = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_assets'
    )
    created_at           = models.DateTimeField(auto_now_add=True)
    updated_at           = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} ({self.status})"

    class Meta:
        ordering = ['-created_at']

    @property
    def annual_depreciation(self):
        if not self.useful_life_years or self.useful_life_years <= 0:
            return Decimal('0.00')

        if self.depreciation_method == self.DepreciationMethod.DECLINING_BALANCE:
            # Double-declining-balance: rate applied to the current book value.
            # The book value shrinks each period, so this returns less over
            # time; the salvage floor is enforced in the depreciation service.
            rate = Decimal('2') / Decimal(self.useful_life_years)
            return Decimal(self.current_value) * rate

        # Straight line
        return (
            Decimal(self.purchase_price) - Decimal(self.salvage_value)
        ) / Decimal(self.useful_life_years)

    @property
    def monthly_depreciation(self):
        return (self.annual_depreciation / Decimal('12')).quantize(Decimal('0.01'))

    def generate_qr(self):
        """Generate and save QR code for this asset"""
        qr_data = f"ASSET-{self.id}-{self.name}-{self.serial_number}"
        qr      = qrcode.make(qr_data)
        buffer  = BytesIO()
        qr.save(buffer, format='PNG')
        self.qr_code.save(
            f'asset_{self.id}_qr.png',
            File(buffer),
            save=True
        )


class DepreciationRecord(models.Model):
    """Monthly depreciation log"""
    asset             = models.ForeignKey(Asset, on_delete=models.CASCADE, related_name='depreciation_records')
    month             = models.PositiveIntegerField()
    year              = models.PositiveIntegerField()
    depreciation_amount = models.DecimalField(max_digits=12, decimal_places=2)
    value_before      = models.DecimalField(max_digits=12, decimal_places=2)
    value_after       = models.DecimalField(max_digits=12, decimal_places=2)
    created_at        = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['asset', 'month', 'year']
        ordering        = ['-year', '-month']

    def __str__(self):
        return f"{self.asset.name} - {self.month}/{self.year} - {self.depreciation_amount}"


class MaintenanceSchedule(models.Model):
    class Frequency(models.TextChoices):
        WEEKLY   = 'WEEKLY',   'Weekly'
        MONTHLY  = 'MONTHLY',  'Monthly'
        QUARTERLY = 'QUARTERLY', 'Quarterly'
        YEARLY   = 'YEARLY',   'Yearly'

    asset            = models.ForeignKey(Asset, on_delete=models.CASCADE, related_name='maintenance_schedules')
    title            = models.CharField(max_length=100)
    description      = models.TextField(blank=True)
    frequency        = models.CharField(max_length=20, choices=Frequency.choices)
    next_due_date    = models.DateField()
    assigned_to      = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='maintenance_tasks'
    )
    is_active        = models.BooleanField(default=True)
    created_at       = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.asset.name} - {self.title} (Due: {self.next_due_date})"

    class Meta:
        ordering = ['next_due_date']
        indexes = [
            models.Index(fields=['is_active', 'next_due_date']),
        ]


class MaintenanceLog(models.Model):
    class Status(models.TextChoices):
        COMPLETED = 'COMPLETED', 'Completed'
        PENDING   = 'PENDING',   'Pending'
        CANCELLED = 'CANCELLED', 'Cancelled'

    asset        = models.ForeignKey(Asset, on_delete=models.CASCADE, related_name='maintenance_logs')
    schedule     = models.ForeignKey(MaintenanceSchedule, on_delete=models.SET_NULL, null=True, blank=True)
    title        = models.CharField(max_length=100)
    description  = models.TextField()
    cost         = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    status       = models.CharField(max_length=20, choices=Status.choices, default=Status.COMPLETED)
    performed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='maintenance_done')
    performed_at = models.DateTimeField()
    next_due_date = models.DateField(null=True, blank=True)
    created_at   = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.asset.name} - {self.title} ({self.status})"

    class Meta:
        ordering = ['-performed_at']