from django.db import models
from accounts.models import Branch


class Menu(models.Model):
    branch = models.OneToOneField(
        Branch,
        on_delete=models.CASCADE,
        related_name='menu'
    )
    name = models.CharField(max_length=100)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.branch.name} - Menu"

    class Meta:
        ordering = ['id']


class MenuSection(models.Model):
    menu = models.ForeignKey(
        Menu,
        on_delete=models.CASCADE,
        related_name='sections'
    )
    name = models.CharField(max_length=100)  # e.g. Starters, Mains, Desserts
    description = models.TextField(blank=True)
    order = models.PositiveIntegerField(default=0)  # for display ordering

    class Meta:
        ordering = ['order']

    def __str__(self):
        return f"{self.menu.branch.name} - {self.name}"


class MenuItem(models.Model):
    class Category(models.TextChoices):
        FOOD = 'FOOD', 'Food'
        DRINK = 'DRINK', 'Drink'
        DESSERT = 'DESSERT', 'Dessert'

    section = models.ForeignKey(
        MenuSection,
        on_delete=models.CASCADE,
        related_name='items'
    )
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    category = models.CharField(
        max_length=20,
        choices=Category.choices,
        default=Category.FOOD
    )
    image = models.ImageField(
        upload_to='menu_items/',
        null=True,
        blank=True
    )
    is_available = models.BooleanField(default=True)
    preparation_time = models.PositiveIntegerField(
        default=15,
        help_text="Preparation time in minutes"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} - {self.price}"