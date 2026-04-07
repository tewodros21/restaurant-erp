from django.shortcuts import render

# Create your views here.
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import Table, TableSeat, SeatingArrangement
from .serializers import TableSerializer, TableSeatSerializer, SeatingArrangementSerializer
from accounts.permissions import IsManager, IsWaiter
import qrcode
from io import BytesIO
from django.core.files import File


class TableListView(generics.ListCreateAPIView):
    serializer_class = TableSerializer
    permission_classes = [IsWaiter]

    def get_queryset(self):
        branch = self.request.user.branch
        status_filter = self.request.query_params.get('status')
        queryset = Table.objects.filter(branch=branch)
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        return queryset


class TableDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = TableSerializer
    permission_classes = [IsManager]
    queryset = Table.objects.all()


class AvailableTablesView(generics.ListAPIView):
    """Get all available tables for a branch"""
    serializer_class = TableSerializer
    permission_classes = [IsWaiter]

    def get_queryset(self):
        return Table.objects.filter(
            branch=self.request.user.branch,
            status=Table.Status.AVAILABLE
        )


class UpdateTableStatusView(APIView):
    """Update table status - used by waiters"""
    permission_classes = [IsWaiter]

    def patch(self, request, pk):
        try:
            table = Table.objects.get(pk=pk, branch=request.user.branch)
            new_status = request.data.get('status')
            if new_status not in Table.Status.values:
                return Response(
                    {'error': 'Invalid status'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            table.status = new_status
            table.save()
            return Response(TableSerializer(table).data)
        except Table.DoesNotExist:
            return Response(
                {'error': 'Table not found'},
                status=status.HTTP_404_NOT_FOUND
            )


class GenerateTableQRView(APIView):
    """Generate QR code for a table"""
    permission_classes = [IsManager]

    def post(self, request, pk):
        try:
            table = Table.objects.get(pk=pk)
            # Generate QR code pointing to the table's order URL
            qr_data = f"https://yourapp.com/order/table/{table.id}/"
            qr = qrcode.make(qr_data)
            buffer = BytesIO()
            qr.save(buffer, format='PNG')
            table.qr_code.save(
                f'table_{table.table_number}_qr.png',
                File(buffer),
                save=True
            )
            return Response({'message': 'QR code generated successfully'})
        except Table.DoesNotExist:
            return Response(
                {'error': 'Table not found'},
                status=status.HTTP_404_NOT_FOUND
            )


class SeatingArrangementListView(generics.ListCreateAPIView):
    serializer_class = SeatingArrangementSerializer
    permission_classes = [IsManager]

    def get_queryset(self):
        return SeatingArrangement.objects.filter(
            branch=self.request.user.branch
        )