from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from .models import (
    Category, Unit, Ingredient,
    Recipe, RecipeIngredient,
    StockTransaction, WastageLog
)
from .serializers import (
    CategorySerializer, UnitSerializer, IngredientSerializer,
    RecipeSerializer, RecipeIngredientSerializer,
    StockTransactionSerializer, WastageLogSerializer
)
from .services import add_stock
from accounts.permissions import IsManager, IsWaiter


class CategoryListView(generics.ListCreateAPIView):
    serializer_class   = CategorySerializer
    permission_classes = [IsManager]
    queryset           = Category.objects.all()


class UnitListView(generics.ListCreateAPIView):
    serializer_class   = UnitSerializer
    permission_classes = [IsManager]
    queryset           = Unit.objects.all()


class IngredientListView(generics.ListCreateAPIView):
    serializer_class   = IngredientSerializer
    permission_classes = [IsManager]

    def get_queryset(self):
        qs = Ingredient.objects.filter(branch=self.request.user.branch)
        # Filter by low stock
        if self.request.query_params.get('low_stock'):
            qs = [i for i in qs if i.is_low_stock]
        return qs


class IngredientDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class   = IngredientSerializer
    permission_classes = [IsManager]
    queryset           = Ingredient.objects.all()


class AddStockView(APIView):
    """Manually add stock for an ingredient"""
    permission_classes = [IsManager]

    def post(self, request, ingredient_id):
        ingredient = get_object_or_404(Ingredient, id=ingredient_id)
        quantity   = request.data.get('quantity')
        notes      = request.data.get('notes', '')

        if not quantity or float(quantity) <= 0:
            return Response(
                {'error': 'Valid quantity required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        add_stock(ingredient, float(quantity), request.user, notes)
        return Response(IngredientSerializer(ingredient).data)


class RecipeListView(generics.ListCreateAPIView):
    serializer_class   = RecipeSerializer
    permission_classes = [IsManager]
    queryset           = Recipe.objects.all()


class RecipeDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class   = RecipeSerializer
    permission_classes = [IsManager]
    queryset           = Recipe.objects.all()


class AddRecipeIngredientView(generics.CreateAPIView):
    serializer_class   = RecipeIngredientSerializer
    permission_classes = [IsManager]


class StockTransactionListView(generics.ListAPIView):
    """View all stock movements"""
    serializer_class   = StockTransactionSerializer
    permission_classes = [IsManager]

    def get_queryset(self):
        return StockTransaction.objects.filter(
            ingredient__branch=self.request.user.branch
        ).order_by('-created_at')


class WastageLogListView(generics.ListCreateAPIView):
    """View and log wastage"""
    serializer_class   = WastageLogSerializer
    permission_classes = [IsManager]

    def get_queryset(self):
        return WastageLog.objects.filter(
            branch=self.request.user.branch
        ).order_by('-created_at')

    def perform_create(self, serializer):
        ingredient = serializer.validated_data['ingredient']
        quantity   = serializer.validated_data['quantity']

        # Deduct from stock when logging wastage
        ingredient.current_stock -= quantity
        ingredient.save()

        StockTransaction.objects.create(
            ingredient       = ingredient,
            transaction_type = 'WASTAGE',
            quantity         = quantity,
            notes            = serializer.validated_data.get('reason', ''),
            created_by       = self.request.user
        )
        serializer.save(branch=self.request.user.branch, logged_by=self.request.user)


class LowStockAlertView(generics.ListAPIView):
    """Get all ingredients that are low on stock"""
    serializer_class   = IngredientSerializer
    permission_classes = [IsManager]

    def get_queryset(self):
        ingredients = Ingredient.objects.filter(branch=self.request.user.branch)
        return [i for i in ingredients if i.is_low_stock]


class ExpiredIngredientView(generics.ListAPIView):
    """Get all expired ingredients"""
    serializer_class   = IngredientSerializer
    permission_classes = [IsManager]

    def get_queryset(self):
        ingredients = Ingredient.objects.filter(branch=self.request.user.branch)
        return [i for i in ingredients if i.is_expired]