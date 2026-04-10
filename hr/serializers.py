from rest_framework import serializers
from .models import (
    Department, EmployeeProfile,
    AttendanceRecord, LeaveRequest, PayrollRecord
)


class DepartmentSerializer(serializers.ModelSerializer):
    class Meta:
        model  = Department
        fields = '__all__'


class EmployeeProfileSerializer(serializers.ModelSerializer):
    employee_name   = serializers.CharField(source='user.get_full_name', read_only=True)
    department_name = serializers.CharField(source='department.name', read_only=True)
    role            = serializers.CharField(source='user.role', read_only=True)

    class Meta:
        model  = EmployeeProfile
        fields = '__all__'


class AttendanceRecordSerializer(serializers.ModelSerializer):
    employee_name = serializers.CharField(source='employee.get_full_name', read_only=True)
    hours_worked  = serializers.ReadOnlyField()
    overtime_hours = serializers.ReadOnlyField()

    class Meta:
        model  = AttendanceRecord
        fields = '__all__'


class LeaveRequestSerializer(serializers.ModelSerializer):
    employee_name = serializers.CharField(source='employee.get_full_name', read_only=True)
    total_days    = serializers.ReadOnlyField()

    class Meta:
        model  = LeaveRequest
        fields = '__all__'


class PayrollRecordSerializer(serializers.ModelSerializer):
    employee_name = serializers.CharField(source='employee.get_full_name', read_only=True)

    class Meta:
        model  = PayrollRecord
        fields = '__all__'