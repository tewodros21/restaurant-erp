from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from .models import (
    AssetCategory, Asset,
    DepreciationRecord,
    MaintenanceSchedule, MaintenanceLog
)
from .serializers import (
    AssetCategorySerializer, AssetSerializer,
    DepreciationRecordSerializer,
    MaintenanceScheduleSerializer, MaintenanceLogSerializer
)
from .services import apply_depreciation_all_assets, get_upcoming_maintenance, record_maintenance
from accounts.permissions import IsManager
from accounts.mixins import BranchScopedQuerysetMixin


class AssetCategoryListView(generics.ListCreateAPIView):
    serializer_class   = AssetCategorySerializer
    permission_classes = [IsManager]
    queryset           = AssetCategory.objects.all()


class AssetListView(generics.ListCreateAPIView):
    serializer_class   = AssetSerializer
    permission_classes = [IsManager]

    def get_queryset(self):
        qs       = Asset.objects.filter(
            branch=self.request.user.branch
        ).select_related('category', 'assigned_to')
        status_f = self.request.query_params.get('status')
        category = self.request.query_params.get('category')
        if status_f:
            qs = qs.filter(status=status_f)
        if category:
            qs = qs.filter(category_id=category)
        return qs

    def perform_create(self, serializer):
        asset = serializer.save(branch=self.request.user.branch)
        # Auto-generate QR code on creation
        asset.generate_qr()


class AssetDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class   = AssetSerializer
    permission_classes = [IsManager]

    def get_queryset(self):
        return Asset.objects.filter(branch=self.request.user.branch)


class GenerateAssetQRView(APIView):
    """Regenerate QR code for an asset"""
    permission_classes = [IsManager]

    def post(self, request, pk):
        asset = get_object_or_404(Asset, pk=pk, branch=request.user.branch)
        asset.generate_qr()
        return Response({'message': f'QR code generated for {asset.name}'})


class ApplyDepreciationView(APIView):
    """Manually trigger monthly depreciation for all branch assets"""
    permission_classes = [IsManager]

    def post(self, request):
        results = apply_depreciation_all_assets(request.user.branch)
        return Response({
            'message': f'Depreciation applied to {len(results)} assets',
            'results': [
                {'asset': r['asset'], 'message': r['message']}
                for r in results
            ]
        })


class DepreciationRecordListView(generics.ListAPIView):
    """View depreciation history for all branch assets"""
    serializer_class   = DepreciationRecordSerializer
    permission_classes = [IsManager]

    def get_queryset(self):
        return DepreciationRecord.objects.filter(
            asset__branch=self.request.user.branch
        ).select_related('asset').order_by('-year', '-month')


class MaintenanceScheduleListView(generics.ListCreateAPIView):
    serializer_class   = MaintenanceScheduleSerializer
    permission_classes = [IsManager]

    def get_queryset(self):
        return MaintenanceSchedule.objects.filter(
            asset__branch=self.request.user.branch
        ).select_related('asset', 'assigned_to')


class MaintenanceScheduleDetailView(BranchScopedQuerysetMixin, generics.RetrieveUpdateDestroyAPIView):
    serializer_class   = MaintenanceScheduleSerializer
    permission_classes = [IsManager]
    queryset           = MaintenanceSchedule.objects.all()
    branch_lookup      = 'asset__branch'


class UpcomingMaintenanceView(APIView):
    """Get maintenance due in the next 7 days"""
    permission_classes = [IsManager]

    def get(self, request):
        days     = int(request.query_params.get('days', 7))
        schedules = get_upcoming_maintenance(request.user.branch, days)
        return Response(MaintenanceScheduleSerializer(schedules, many=True).data)


class MaintenanceLogListView(generics.ListCreateAPIView):
    serializer_class   = MaintenanceLogSerializer
    permission_classes = [IsManager]

    def get_queryset(self):
        return MaintenanceLog.objects.filter(
            asset__branch=self.request.user.branch
        ).select_related('asset', 'performed_by').order_by('-performed_at')

    def perform_create(self, serializer):
        log = serializer.save(performed_by=self.request.user)
        record_maintenance(log)


class MaintenanceLogDetailView(BranchScopedQuerysetMixin, generics.RetrieveUpdateAPIView):
    serializer_class   = MaintenanceLogSerializer
    permission_classes = [IsManager]
    queryset           = MaintenanceLog.objects.all()
    branch_lookup      = 'asset__branch'