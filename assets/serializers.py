from rest_framework import serializers
from .models import (
    AssetCategory, Asset,
    DepreciationRecord,
    MaintenanceSchedule, MaintenanceLog
)


class AssetCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model  = AssetCategory
        fields = '__all__'


class AssetSerializer(serializers.ModelSerializer):
    category_name        = serializers.CharField(source='category.name', read_only=True)
    annual_depreciation  = serializers.ReadOnlyField()
    monthly_depreciation = serializers.ReadOnlyField()
    assigned_to_name     = serializers.CharField(source='assigned_to.get_full_name', read_only=True)

    class Meta:
        model  = Asset
        fields = '__all__'


class DepreciationRecordSerializer(serializers.ModelSerializer):
    asset_name = serializers.CharField(source='asset.name', read_only=True)

    class Meta:
        model  = DepreciationRecord
        fields = '__all__'


class MaintenanceScheduleSerializer(serializers.ModelSerializer):
    asset_name      = serializers.CharField(source='asset.name', read_only=True)
    assigned_to_name = serializers.CharField(source='assigned_to.get_full_name', read_only=True)

    class Meta:
        model  = MaintenanceSchedule
        fields = '__all__'


class MaintenanceLogSerializer(serializers.ModelSerializer):
    asset_name       = serializers.CharField(source='asset.name', read_only=True)
    performed_by_name = serializers.CharField(source='performed_by.get_full_name', read_only=True)

    class Meta:
        model  = MaintenanceLog
        fields = '__all__'