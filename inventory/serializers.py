from rest_framework import serializers
from .models import (
    Category, Unit, Ingredient,
    Recipe, RecipeIngredient,
    StockTransaction, WastageLog
)


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model  = Category
        fields = '__all__'


class UnitSerializer(serializers.ModelSerializer):
    class Meta:
        model  = Unit
        fields = '__all__'


class IngredientSerializer(serializers.ModelSerializer):
    is_low_stock  = serializers.ReadOnlyField()
    is_expired    = serializers.ReadOnlyField()
    unit_name     = serializers.CharField(source='unit.abbreviation', read_only=True)
    category_name = serializers.CharField(source='category.name', read_only=True)

    class Meta:
        model  = Ingredient
        fields = '__all__'


class RecipeIngredientSerializer(serializers.ModelSerializer):
    ingredient_name = serializers.CharField(source='ingredient.name', read_only=True)
    unit            = serializers.CharField(source='ingredient.unit.abbreviation', read_only=True)

    class Meta:
        model  = RecipeIngredient
        fields = '__all__'


class RecipeSerializer(serializers.ModelSerializer):
    ingredients    = RecipeIngredientSerializer(many=True, read_only=True)
    menu_item_name = serializers.CharField(source='menu_item.name', read_only=True)

    class Meta:
        model  = Recipe
        fields = '__all__'


class StockTransactionSerializer(serializers.ModelSerializer):
    ingredient_name = serializers.CharField(source='ingredient.name', read_only=True)
    created_by_name = serializers.CharField(source='created_by.get_full_name', read_only=True)

    class Meta:
        model  = StockTransaction
        fields = '__all__'


class WastageLogSerializer(serializers.ModelSerializer):
    ingredient_name = serializers.CharField(source='ingredient.name', read_only=True)
    logged_by_name  = serializers.CharField(source='logged_by.get_full_name', read_only=True)

    class Meta:
        model  = WastageLog
        fields = '__all__'