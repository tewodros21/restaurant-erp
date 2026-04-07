from rest_framework import serializers
from .models import Table, TableSeat, SeatingArrangement


class TableSeatSerializer(serializers.ModelSerializer):
    class Meta:
        model = TableSeat
        fields = '__all__'


class TableSerializer(serializers.ModelSerializer):
    seats = TableSeatSerializer(many=True, read_only=True)
    status_display = serializers.CharField(
        source='get_status_display',
        read_only=True
    )

    class Meta:
        model = Table
        fields = '__all__'


class SeatingArrangementSerializer(serializers.ModelSerializer):
    tables = TableSerializer(many=True, read_only=True)

    class Meta:
        model = SeatingArrangement
        fields = '__all__'