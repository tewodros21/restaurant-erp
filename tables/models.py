from django.db import models
from accounts.models import Branch


class SeatingArrangement(models.Model):
    """Represents a section/area in the restaurant"""
    branch = models.ForeignKey(
        Branch,
        on_delete=models.CASCADE,
        related_name='seating_arrangements'
    )
    name = models.CharField(max_length=100)  # e.g. Indoor, Outdoor, VIP
    description = models.TextField(blank=True)

    def __str__(self):
        return f"{self.branch.name} - {self.name}"

    class Meta:
        ordering = ['id']


class Table(models.Model):
    class Status(models.TextChoices):
        AVAILABLE = 'AVAILABLE', 'Available'
        OCCUPIED = 'OCCUPIED', 'Occupied'
        RESERVED = 'RESERVED', 'Reserved'
        CLEANING = 'CLEANING', 'Cleaning'
        OUT_OF_SERVICE = 'OUT_OF_SERVICE', 'Out of Service'

    branch = models.ForeignKey(
        Branch,
        on_delete=models.CASCADE,
        related_name='tables'
    )
    seating_arrangement = models.ForeignKey(
        SeatingArrangement,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='tables'
    )
    table_number = models.CharField(max_length=10)  # e.g. T1, T2, VIP1
    capacity = models.PositiveIntegerField()          # max seats
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.AVAILABLE
    )
    qr_code = models.ImageField(
        upload_to='table_qrcodes/',
        null=True,
        blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['branch', 'table_number']
        ordering = ['table_number']
        indexes = [
            models.Index(fields=['branch', 'status']),
        ]

    def __str__(self):
        return f"Table {self.table_number} - {self.branch.name} ({self.status})"

    @property
    def is_available(self):
        return self.status == self.Status.AVAILABLE


class TableSeat(models.Model):
    table = models.ForeignKey(
        Table,
        on_delete=models.CASCADE,
        related_name='seats'
    )
    seat_number = models.PositiveIntegerField()

    class Meta:
        unique_together = ['table', 'seat_number']
        ordering = ['id']

    def __str__(self):
        return f"Table {self.table.table_number} - Seat {self.seat_number}"