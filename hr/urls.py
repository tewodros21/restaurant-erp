from django.urls import path
from . import views

urlpatterns = [
    # Departments
    path('departments/', views.DepartmentListView.as_view(), name='department-list'),

    # Employee Profiles
    path('profiles/', views.EmployeeProfileListView.as_view(), name='profile-list'),
    path('profiles/<int:pk>/', views.EmployeeProfileDetailView.as_view(), name='profile-detail'),

    # Attendance
    path('attendance/clock-in/', views.ClockInView.as_view(), name='clock-in'),
    path('attendance/clock-out/', views.ClockOutView.as_view(), name='clock-out'),
    path('attendance/', views.AttendanceListView.as_view(), name='attendance-list'),
    path('attendance/me/', views.MyAttendanceView.as_view(), name='my-attendance'),

    # Leave
    path('leave/', views.LeaveRequestListView.as_view(), name='leave-list'),
    path('leave/<int:pk>/approve/', views.LeaveRequestApproveView.as_view(), name='leave-approve'),

    # Payroll
    path('payroll/', views.PayrollListView.as_view(), name='payroll-list'),
    path('payroll/me/', views.MyPayrollView.as_view(), name='my-payroll'),
    path('payroll/generate/<int:employee_id>/', views.GeneratePayrollView.as_view(), name='generate-payroll'),
    path('payroll/<int:pk>/confirm/', views.ConfirmPayrollView.as_view(), name='confirm-payroll'),
]