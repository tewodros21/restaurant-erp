from django.db import models
from accounts.models import Branch
from menu.models import MenuItem


class Category(models.Model):
    """Ingredient categories e.g. Meat, Dairy, Vegetables"""
    name        = models.CharField(max_length=100)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name


class Unit(models.Model):
    """Units of measurement e.g. kg, g, ml, L, pieces"""
    name         = models.CharField(max_length=50)   # e.g. Kilogram
    abbreviation = models.CharField(max_length=10)   # e.g. kg

    def __str__(self):
        return self.abbreviation


class Ingredient(models.Model):
    """Stock item / ingredient"""
    branch            = models.ForeignKey(Branch, on_delete=models.CASCADE, related_name='ingredients')
    category          = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True)
    unit              = models.ForeignKey(Unit, on_delete=models.SET_NULL, null=True)
    name              = models.CharField(max_length=100)
    current_stock     = models.DecimalField(max_digits=10, decimal_places=3, default=0)
    minimum_stock     = models.DecimalField(max_digits=10, decimal_places=3, default=0)
    cost_per_unit     = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    expiration_date   = models.DateField(null=True, blank=True)
    is_active         = models.BooleanField(default=True)
    created_at        = models.DateTimeField(auto_now_add=True)
    updated_at        = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.current_stock} {self.unit})"

    @property
    def is_low_stock(self):
        return self.current_stock <= self.minimum_stock

    @property
    def is_expired(self):
        from django.utils import timezone
        if self.expiration_date:
            return self.expiration_date < timezone.now().date()
        return False


class Recipe(models.Model):
    """Links a menu item to its ingredients"""
    menu_item   = models.OneToOneField(MenuItem, on_delete=models.CASCADE, related_name='recipe')
    description = models.TextField(blank=True)
    created_at  = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Recipe: {self.menu_item.name}"


class RecipeIngredient(models.Model):
    """Each ingredient in a recipe with quantity"""
    recipe     = models.ForeignKey(Recipe, on_delete=models.CASCADE, related_name='ingredients')
    ingredient = models.ForeignKey(Ingredient, on_delete=models.CASCADE)
    quantity   = models.DecimalField(max_digits=10, decimal_places=3)

    def __str__(self):
        return f"{self.quantity} {self.ingredient.unit} of {self.ingredient.name}"


class StockTransaction(models.Model):
    """Log of all stock movements"""
    class TransactionType(models.TextChoices):
        IN        = 'IN',        'Stock In'
        OUT       = 'OUT',       'Stock Out'
        WASTAGE   = 'WASTAGE',   'Wastage'
        ADJUST    = 'ADJUST',    'Adjustment'

    ingredient       = models.ForeignKey(Ingredient, on_delete=models.CASCADE, related_name='transactions')
    transaction_type = models.CharField(max_length=20, choices=TransactionType.choices)
    quantity         = models.DecimalField(max_digits=10, decimal_places=3)
    notes            = models.TextField(blank=True)
    created_by       = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True)
    created_at       = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.transaction_type} - {self.ingredient.name} - {self.quantity}"


class WastageLog(models.Model):
    """Tracks spoiled or wasted inventory"""
    branch     = models.ForeignKey(Branch, on_delete=models.CASCADE, related_name='wastage_logs')
    ingredient = models.ForeignKey(Ingredient, on_delete=models.CASCADE)
    quantity   = models.DecimalField(max_digits=10, decimal_places=3)
    reason     = models.TextField()
    logged_by  = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Wastage: {self.ingredient.name} - {self.quantity}"