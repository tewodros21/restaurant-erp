from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from .models import Order, Meal, MealItem, KOT, BOT
from .serializers import (
    OrderSerializer, CreateOrderSerializer,
    MealSerializer, MealItemSerializer,
    KOTSerializer, BOTSerializer
)
from accounts.permissions import IsWaiter, IsChef, IsManager
from tables.models import Table


class OrderListView(generics.ListAPIView):
    """List all orders for the branch"""
    serializer_class   = OrderSerializer
    permission_classes = [IsWaiter]

    def get_queryset(self):
        branch = self.request.user.branch
        status_filter = self.request.query_params.get('status')
        qs = Order.objects.filter(branch=branch).order_by('-created_at')
        if status_filter:
            qs = qs.filter(status=status_filter)
        return qs


class CreateOrderView(generics.CreateAPIView):
    """Waiter creates a new order for a table"""
    serializer_class   = CreateOrderSerializer
    permission_classes = [IsWaiter]

    def perform_create(self, serializer):
        order = serializer.save()
        # Mark table as occupied
        if order.table:
            order.table.status = Table.Status.OCCUPIED
            order.table.save()


class OrderDetailView(generics.RetrieveUpdateAPIView):
    """Get or update a specific order"""
    serializer_class   = OrderSerializer
    permission_classes = [IsWaiter]
    queryset           = Order.objects.all()


class AddMealView(APIView):
    """Add a meal (per seat) to an order"""
    permission_classes = [IsWaiter]

    def post(self, request, order_id):
        order = get_object_or_404(Order, id=order_id, branch=request.user.branch)
        seat_label = request.data.get('seat_label', 'Seat 1')
        notes      = request.data.get('notes', '')
        meal = Meal.objects.create(order=order, seat_label=seat_label, notes=notes)
        return Response(MealSerializer(meal).data, status=status.HTTP_201_CREATED)


class AddMealItemView(APIView):
    """Add item to a meal"""
    permission_classes = [IsWaiter]

    def post(self, request, meal_id):
        meal        = get_object_or_404(Meal, id=meal_id)
        menu_item_id = request.data.get('menu_item_id')
        quantity    = request.data.get('quantity', 1)
        notes       = request.data.get('notes', '')

        from menu.models import MenuItem
        menu_item = get_object_or_404(MenuItem, id=menu_item_id)

        # Determine if food or drink
        item_type = 'DRINK' if menu_item.category == 'DRINK' else 'FOOD'

        meal_item = MealItem.objects.create(
            meal       = meal,
            menu_item  = menu_item,
            quantity   = quantity,
            unit_price = menu_item.price,
            item_type  = item_type,
            notes      = notes
        )
        return Response(MealItemSerializer(meal_item).data, status=status.HTTP_201_CREATED)


class SubmitOrderView(APIView):
    """Submit order — generates KOT and BOT"""
    permission_classes = [IsWaiter]

    def post(self, request, order_id):
        order = get_object_or_404(Order, id=order_id, branch=request.user.branch)

        if order.status != 'PENDING':
            return Response(
                {'error': 'Order already submitted'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Separate food and drink items
        food_items  = []
        drink_items = []

        for meal in order.meals.all():
            for item in meal.items.all():
                if item.item_type == 'FOOD':
                    food_items.append(item)
                else:
                    drink_items.append(item)

        # Generate KOT for food items
        if food_items:
            kot = KOT.objects.create(order=order)
            kot.items.set(food_items)

        # Generate BOT for drink items
        if drink_items:
            bot = BOT.objects.create(order=order)
            bot.items.set(drink_items)

        # Update order status
        order.status = 'CONFIRMED'
        order.save()

        return Response({
            'message': 'Order submitted successfully',
            'kot_generated': bool(food_items),
            'bot_generated': bool(drink_items),
            'order': OrderSerializer(order).data
        })


class UpdateMealItemStatusView(APIView):
    """Chef/Bartender updates item status"""
    permission_classes = [IsChef]

    def patch(self, request, item_id):
        item       = get_object_or_404(MealItem, id=item_id)
        new_status = request.data.get('status')

        if new_status not in MealItem.Status.values:
            return Response(
                {'error': 'Invalid status'},
                status=status.HTTP_400_BAD_REQUEST
            )

        item.status = new_status
        item.save()

        # Check if all items in order are READY → update order status
        order = item.meal.order
        all_items = MealItem.objects.filter(meal__order=order)
        if all(i.status == 'READY' for i in all_items):
            order.status = 'READY'
            order.save()

        return Response(MealItemSerializer(item).data)


class KOTListView(generics.ListAPIView):
    """Chef views all pending KOTs"""
    serializer_class   = KOTSerializer
    permission_classes = [IsChef]

    def get_queryset(self):
        return KOT.objects.filter(
            order__branch=self.request.user.branch,
            order__status__in=['CONFIRMED', 'PREPARING']
        ).order_by('created_at')


class BOTListView(generics.ListAPIView):
    """Bartender views all pending BOTs"""
    serializer_class   = BOTSerializer
    permission_classes = [IsWaiter]

    def get_queryset(self):
        return BOT.objects.filter(
            order__branch=self.request.user.branch,
            order__status__in=['CONFIRMED', 'PREPARING']
        ).order_by('created_at')


class UpdateOrderStatusView(APIView):
    """Update overall order status"""
    permission_classes = [IsWaiter]

    def patch(self, request, order_id):
        order      = get_object_or_404(Order, id=order_id, branch=request.user.branch)
        new_status = request.data.get('status')

        if new_status not in Order.Status.values:
            return Response(
                {'error': 'Invalid status'},
                status=status.HTTP_400_BAD_REQUEST
            )

        order.status = new_status
        order.save()

        # If completed, free up the table
        if new_status == 'COMPLETED':
            if order.table:
                order.table.status = Table.Status.CLEANING
                order.table.save()

        return Response(OrderSerializer(order).data)