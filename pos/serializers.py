from rest_framework import serializers
from .models import Order, Meal, MealItem, KOT, BOT, Reservation, Bill, BillItem, Payment
from menu.serializers import MenuItemSerializer


class MealItemSerializer(serializers.ModelSerializer):
    subtotal        = serializers.ReadOnlyField()
    menu_item_name  = serializers.CharField(source='menu_item.name', read_only=True)

    class Meta:
        model  = MealItem
        fields = '__all__'


class MealSerializer(serializers.ModelSerializer):
    items = MealItemSerializer(many=True, read_only=True)

    class Meta:
        model  = Meal
        fields = '__all__'


class OrderSerializer(serializers.ModelSerializer):
    meals       = MealSerializer(many=True, read_only=True)
    total_price = serializers.ReadOnlyField()
    waiter_name = serializers.CharField(source='waiter.get_full_name', read_only=True)
    table_number = serializers.CharField(source='table.table_number', read_only=True)

    class Meta:
        model  = Order
        fields = '__all__'


class CreateOrderSerializer(serializers.ModelSerializer):
    class Meta:
        model  = Order
        fields = ['table', 'order_type', 'notes']

    def create(self, validated_data):
        request = self.context['request']
        validated_data['waiter']  = request.user
        validated_data['branch']  = request.user.branch
        validated_data['status']  = 'PENDING'
        return super().create(validated_data)


class KOTSerializer(serializers.ModelSerializer):
    items = MealItemSerializer(many=True, read_only=True)

    class Meta:
        model  = KOT
        fields = '__all__'


class BOTSerializer(serializers.ModelSerializer):
    items = MealItemSerializer(many=True, read_only=True)

    class Meta:
        model  = BOT
        fields = '__all__'

class ReservationSerializer(serializers.ModelSerializer):
    created_by_name = serializers.CharField(
        source='created_by.get_full_name', read_only=True
    )
    table_number = serializers.CharField(
        source='table.table_number', read_only=True
    )

    class Meta:
        model  = Reservation
        fields = '__all__'


class BillItemSerializer(serializers.ModelSerializer):
    class Meta:
        model  = BillItem
        fields = '__all__'


class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model  = Payment
        fields = '__all__'


class BillSerializer(serializers.ModelSerializer):
    items   = BillItemSerializer(many=True, read_only=True)
    payment = PaymentSerializer(read_only=True)

    class Meta:
        model  = Bill
        fields = '__all__'