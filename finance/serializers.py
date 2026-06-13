from rest_framework import serializers
from .models import ExpenseCategory, Expense, DailyReport


class ExpenseCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model  = ExpenseCategory
        fields = '__all__'


class ExpenseSerializer(serializers.ModelSerializer):
    category_name   = serializers.CharField(source='category.name', read_only=True)
    created_by_name = serializers.CharField(
        source='created_by.get_full_name',
        read_only=True
    )

    class Meta:
        model  = Expense
        fields = '__all__'
        # Make auto-set fields optional. `status` is read-only so a creator
        # cannot POST status='APPROVED' and bypass ApproveExpenseView.
        read_only_fields = ['branch', 'created_by', 'approved_by', 'status']


class DailyReportSerializer(serializers.ModelSerializer):
    branch_name = serializers.CharField(source='branch.name', read_only=True)

    class Meta:
        model  = DailyReport
        fields = '__all__'