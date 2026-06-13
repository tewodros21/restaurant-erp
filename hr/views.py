from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from django.utils import timezone
from .models import (
    Department, EmployeeProfile,
    AttendanceRecord, LeaveRequest, PayrollRecord
)
from .serializers import (
    DepartmentSerializer, EmployeeProfileSerializer,
    AttendanceRecordSerializer, LeaveRequestSerializer,
    PayrollRecordSerializer
)
from .services import clock_in, clock_out, generate_payroll
from accounts.models import User
from accounts.permissions import IsManager
from accounts.mixins import BranchScopedQuerysetMixin


def _branch_scoped(qs, user, lookup='branch'):
    """Limit a queryset to the user's branch (ADMIN sees all)."""
    if getattr(user, 'role', None) == 'ADMIN':
        return qs
    if getattr(user, 'branch', None) is None:
        return qs.none()
    return qs.filter(**{lookup: user.branch})


class DepartmentListView(generics.ListCreateAPIView):
    serializer_class   = DepartmentSerializer
    permission_classes = [IsManager]

    def get_queryset(self):
        return Department.objects.filter(branch=self.request.user.branch)


class EmployeeProfileListView(generics.ListCreateAPIView):
    serializer_class   = EmployeeProfileSerializer
    permission_classes = [IsManager]

    def get_queryset(self):
        return EmployeeProfile.objects.filter(
            user__branch=self.request.user.branch
        ).select_related('user', 'department')


class EmployeeProfileDetailView(BranchScopedQuerysetMixin, generics.RetrieveUpdateAPIView):
    serializer_class   = EmployeeProfileSerializer
    permission_classes = [IsManager]
    queryset           = EmployeeProfile.objects.all()
    branch_lookup      = 'user__branch'


class ClockInView(APIView):
    """Employee clocks in"""
    def post(self, request):
        record, message = clock_in(request.user)
        if record:
            return Response({
                'message': message,
                'record':  AttendanceRecordSerializer(record).data
            })
        return Response(
            {'error': message},
            status=status.HTTP_400_BAD_REQUEST
        )


class ClockOutView(APIView):
    """Employee clocks out"""
    def post(self, request):
        record, message = clock_out(request.user)
        if record:
            return Response({
                'message': message,
                'record':  AttendanceRecordSerializer(record).data
            })
        return Response(
            {'error': message},
            status=status.HTTP_400_BAD_REQUEST
        )


class AttendanceListView(generics.ListAPIView):
    """Manager views attendance for branch"""
    serializer_class   = AttendanceRecordSerializer
    permission_classes = [IsManager]

    def get_queryset(self):
        qs = AttendanceRecord.objects.filter(
            employee__branch=self.request.user.branch
        ).select_related('employee')
        # Filter by employee
        employee_id = self.request.query_params.get('employee_id')
        if employee_id:
            qs = qs.filter(employee_id=employee_id)
        # Filter by month/year
        month = self.request.query_params.get('month')
        year  = self.request.query_params.get('year')
        if month and year:
            qs = qs.filter(date__month=month, date__year=year)
        return qs


class MyAttendanceView(generics.ListAPIView):
    """Employee views their own attendance"""
    serializer_class = AttendanceRecordSerializer

    def get_queryset(self):
        return AttendanceRecord.objects.filter(employee=self.request.user)


class LeaveRequestListView(generics.ListCreateAPIView):
    serializer_class = LeaveRequestSerializer

    def get_queryset(self):
        user = self.request.user
        if user.role in ['ADMIN', 'MANAGER']:
            return LeaveRequest.objects.filter(employee__branch=user.branch)
        return LeaveRequest.objects.filter(employee=user)

    def perform_create(self, serializer):
        serializer.save(employee=self.request.user)


class LeaveRequestApproveView(APIView):
    """Manager approves or rejects leave"""
    permission_classes = [IsManager]

    def patch(self, request, pk):
        leave      = get_object_or_404(
            _branch_scoped(LeaveRequest.objects.all(), request.user, 'employee__branch'),
            pk=pk
        )
        new_status = request.data.get('status')  # APPROVED or REJECTED

        if new_status not in ['APPROVED', 'REJECTED']:
            return Response(
                {'error': 'Status must be APPROVED or REJECTED'},
                status=status.HTTP_400_BAD_REQUEST
            )

        leave.status      = new_status
        leave.approved_by = request.user
        leave.save()
        return Response(LeaveRequestSerializer(leave).data)


class GeneratePayrollView(APIView):
    """Generate payroll for an employee"""
    permission_classes = [IsManager]

    def post(self, request, employee_id):
        employee = get_object_or_404(
            _branch_scoped(User.objects.all(), request.user), id=employee_id
        )
        month    = request.data.get('month', timezone.now().month)
        year     = request.data.get('year', timezone.now().year)

        payroll, message = generate_payroll(employee, month, year)
        if payroll:
            return Response({
                'message': message,
                'payroll': PayrollRecordSerializer(payroll).data
            })
        return Response({'error': message}, status=status.HTTP_400_BAD_REQUEST)


class PayrollListView(generics.ListAPIView):
    """List all payroll records for branch"""
    serializer_class   = PayrollRecordSerializer
    permission_classes = [IsManager]

    def get_queryset(self):
        return PayrollRecord.objects.filter(
            employee__branch=self.request.user.branch
        ).select_related('employee')


class ConfirmPayrollView(APIView):
    """Confirm and mark payroll as paid"""
    permission_classes = [IsManager]

    def patch(self, request, pk):
        payroll = get_object_or_404(
            _branch_scoped(PayrollRecord.objects.all(), request.user, 'employee__branch'),
            pk=pk
        )
        payroll.status  = 'PAID'
        payroll.paid_at = timezone.now()
        payroll.save()
        return Response(PayrollRecordSerializer(payroll).data)


class MyPayrollView(generics.ListAPIView):
    """Employee views their own payslips"""
    serializer_class = PayrollRecordSerializer

    def get_queryset(self):
        return PayrollRecord.objects.filter(employee=self.request.user)