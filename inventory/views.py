from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from django.db.models import F
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
from accounts.permissions import IsManager
from accounts.mixins import BranchScopedQuerysetMixin
from decimal import Decimal, InvalidOperation


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
        qs = Ingredient.objects.filter(
            branch=self.request.user.branch
        ).select_related('unit', 'category')
        # Filter by low stock in the DB (a Python list would break pagination)
        if self.request.query_params.get('low_stock'):
            qs = qs.filter(current_stock__lte=F('minimum_stock'))
        return qs


class IngredientDetailView(BranchScopedQuerysetMixin, generics.RetrieveUpdateDestroyAPIView):
    serializer_class   = IngredientSerializer
    permission_classes = [IsManager]
    queryset           = Ingredient.objects.all()


class AddStockView(APIView):
    """Manually add stock for an ingredient"""
    permission_classes = [IsManager]

    def post(self, request, ingredient_id):
        ingredient = get_object_or_404(
            Ingredient, id=ingredient_id, branch=request.user.branch
        )
        notes = request.data.get('notes', '')

        # Stock is a Decimal field — parse as Decimal, never float.
        try:
            quantity = Decimal(str(request.data.get('quantity', '')))
        except (InvalidOperation, TypeError, ValueError):
            return Response(
                {'error': 'Valid quantity required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if quantity <= 0:
            return Response(
                {'error': 'Valid quantity required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        add_stock(ingredient, quantity, request.user, notes)
        ingredient.refresh_from_db()
        return Response(IngredientSerializer(ingredient).data)


class RecipeListView(generics.ListCreateAPIView):
    serializer_class   = RecipeSerializer
    permission_classes = [IsManager]
    queryset           = Recipe.objects.all()


class RecipeDetailView(BranchScopedQuerysetMixin, generics.RetrieveUpdateDestroyAPIView):
    serializer_class   = RecipeSerializer
    permission_classes = [IsManager]
    queryset           = Recipe.objects.all()
    branch_lookup      = 'menu_item__section__menu__branch'


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
        ).select_related('ingredient', 'created_by').order_by('-created_at')


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
        return Ingredient.objects.filter(
            branch=self.request.user.branch,
            current_stock__lte=F('minimum_stock'),
        ).select_related('unit', 'category')


class ExpiredIngredientView(generics.ListAPIView):
    """Get all expired ingredients"""
    serializer_class   = IngredientSerializer
    permission_classes = [IsManager]

    def get_queryset(self):
        from django.utils import timezone
        return Ingredient.objects.filter(
            branch=self.request.user.branch,
            expiration_date__lt=timezone.localdate(),
        ).select_related('unit', 'category')