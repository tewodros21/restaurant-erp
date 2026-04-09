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
from .models import Reservation, Bill, BillItem, Payment, Notification
from .serializers import ReservationSerializer, BillSerializer, PaymentSerializer
from django.utils import timezone
from accounts.permissions import IsCashier


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

class ReservationListView(generics.ListCreateAPIView):
    """List all reservations or create a new one"""
    serializer_class   = ReservationSerializer
    permission_classes = [IsWaiter]

    def get_queryset(self):
        branch = self.request.user.branch
        date   = self.request.query_params.get('date')
        qs     = Reservation.objects.filter(branch=branch)
        if date:
            qs = qs.filter(reservation_date=date)
        return qs

    def perform_create(self, serializer):
        reservation = serializer.save(
            branch     = self.request.user.branch,
            created_by = self.request.user
        )
        # Mark table as reserved
        if reservation.table:
            reservation.table.status = Table.Status.RESERVED
            reservation.table.save()

        # Send confirmation notification
        self._send_notification(reservation, 'RESERVATION_CONFIRMED')

    def _send_notification(self, reservation, notif_type):
        messages = {
            'RESERVATION_CONFIRMED': (
                f"Dear {reservation.customer_name}, your reservation at "
                f"{reservation.reservation_date} {reservation.reservation_time} "
                f"has been confirmed. Table: {reservation.table}."
            ),
            'RESERVATION_CANCELLED': (
                f"Dear {reservation.customer_name}, your reservation on "
                f"{reservation.reservation_date} has been cancelled."
            ),
        }
        Notification.objects.create(
            type      = notif_type,
            recipient = reservation.customer_phone,
            message   = messages.get(notif_type, '')
        )


class ReservationDetailView(generics.RetrieveUpdateAPIView):
    serializer_class   = ReservationSerializer
    permission_classes = [IsWaiter]
    queryset           = Reservation.objects.all()


class CancelReservationView(APIView):
    """Cancel a reservation"""
    permission_classes = [IsWaiter]

    def post(self, request, pk):
        reservation = get_object_or_404(
            Reservation, pk=pk, branch=request.user.branch
        )

        if reservation.status == 'CANCELLED':
            return Response(
                {'error': 'Reservation already cancelled'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Cancel reservation
        reservation.status = 'CANCELLED'
        reservation.save()

        # Free the table
        if reservation.table:
            reservation.table.status = Table.Status.AVAILABLE
            reservation.table.save()

        # Send cancellation notification
        Notification.objects.create(
            type      = 'RESERVATION_CANCELLED',
            recipient = reservation.customer_phone,
            message   = (
                f"Dear {reservation.customer_name}, your reservation on "
                f"{reservation.reservation_date} has been cancelled."
            )
        )

        return Response({
            'message': 'Reservation cancelled successfully',
            'reservation': ReservationSerializer(reservation).data
        })


class CheckInReservationView(APIView):
    """Check in a customer for their reservation"""
    permission_classes = [IsWaiter]

    def post(self, request, pk):
        reservation = get_object_or_404(
            Reservation, pk=pk, branch=request.user.branch
        )

        if reservation.status != 'CONFIRMED':
            return Response(
                {'error': 'Reservation is not in confirmed state'},
                status=status.HTTP_400_BAD_REQUEST
            )

        reservation.status = 'CHECKED_IN'
        reservation.save()

        # Mark table as occupied
        if reservation.table:
            reservation.table.status = Table.Status.OCCUPIED
            reservation.table.save()

        return Response({
            'message': f'{reservation.customer_name} checked in successfully',
            'reservation': ReservationSerializer(reservation).data
        })


class AvailableTablesForReservationView(APIView):
    """Find available tables for a given date, time, and guest count"""
    permission_classes = [IsWaiter]

    def get(self, request):
        date        = request.query_params.get('date')
        time        = request.query_params.get('time')
        guest_count = int(request.query_params.get('guest_count', 1))
        branch      = request.user.branch

        if not date or not time:
            return Response(
                {'error': 'date and time are required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Get tables already reserved at this date/time
        reserved_table_ids = Reservation.objects.filter(
            branch           = branch,
            reservation_date = date,
            reservation_time = time,
            status__in       = ['CONFIRMED', 'CHECKED_IN']
        ).values_list('table_id', flat=True)

        # Find available tables with enough capacity
        available_tables = Table.objects.filter(
            branch   = branch,
            capacity__gte = guest_count
        ).exclude(id__in=reserved_table_ids)

        from tables.serializers import TableSerializer
        return Response(TableSerializer(available_tables, many=True).data)


# ─── BILLING VIEWS ────────────────────────────────────────────────

class GenerateBillView(APIView):
    """Generate a bill for a completed order"""
    permission_classes = [IsCashier]

    def post(self, request, order_id):
        order = get_object_or_404(Order, id=order_id, branch=request.user.branch)

        # Check if bill already exists
        if hasattr(order, 'bill'):
            return Response(
                {'error': 'Bill already generated', 'bill': BillSerializer(order.bill).data},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Create bill
        bill = Bill.objects.create(order=order, branch=request.user.branch)

        # Create bill items from all meal items
        for meal in order.meals.all():
            for item in meal.items.all():
                BillItem.objects.create(
                    bill       = bill,
                    meal_item  = item,
                    name       = item.menu_item.name,
                    quantity   = item.quantity,
                    unit_price = item.unit_price,
                    subtotal   = item.subtotal
                )

        # Calculate totals
        bill.calculate()

        return Response(BillSerializer(bill).data, status=status.HTTP_201_CREATED)


class BillDetailView(generics.RetrieveAPIView):
    """Get bill details"""
    serializer_class   = BillSerializer
    permission_classes = [IsCashier]
    queryset           = Bill.objects.all()


class ProcessPaymentView(APIView):
    """Process payment for a bill"""
    permission_classes = [IsCashier]

    def post(self, request, bill_id):
        bill        = get_object_or_404(Bill, id=bill_id)
        method      = request.data.get('method')
        amount_paid = float(request.data.get('amount_paid', 0))
        reference   = request.data.get('reference_code', '')

        if bill.status == 'PAID':
            return Response(
                {'error': 'Bill already paid'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if amount_paid < float(bill.total):
            return Response(
                {'error': f'Insufficient amount. Total is {bill.total}'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if method not in Payment.Method.values:
            return Response(
                {'error': 'Invalid payment method'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Create payment record
        change = amount_paid - float(bill.total)
        payment = Payment.objects.create(
            bill           = bill,
            method         = method,
            amount_paid    = amount_paid,
            change_given   = change,
            reference_code = reference,
            processed_by   = request.user
        )

        # Mark bill as paid
        bill.status = 'PAID'
        bill.save()

        # Mark order as completed & free table
        order = bill.order
        order.status = 'COMPLETED'
        order.save()

        if order.table:
            order.table.status = Table.Status.CLEANING
            order.table.save()

        return Response({
            'message':  'Payment processed successfully',
            'change':   change,
            'bill':     BillSerializer(bill).data,
            'payment':  PaymentSerializer(payment).data
        })