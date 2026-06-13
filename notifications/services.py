from .models import Notification
from accounts.models import User, Branch


def notify_user(recipient, branch, type, title, message, priority='MEDIUM', data=None):
    """Create a single notification for a user"""
    return Notification.objects.create(
        recipient = recipient,
        branch    = branch,
        type      = type,
        title     = title,
        message   = message,
        priority  = priority,
        data      = data or {}
    )


def notify_managers(branch, type, title, message, priority='MEDIUM', data=None):
    """Send notification to all managers in a branch"""
    managers = User.objects.filter(
        branch = branch,
        role__in = ['ADMIN', 'MANAGER'],
        is_active = True
    )
    notifications = []
    for manager in managers:
        n = notify_user(manager, branch, type, title, message, priority, data)
        notifications.append(n)
    return notifications


def send_low_stock_alert(ingredient):
    """Notify managers when ingredient stock is low"""
    notify_managers(
        branch    = ingredient.branch,
        type      = 'LOW_STOCK',
        title     = f'Low Stock: {ingredient.name}',
        message   = (
            f'{ingredient.name} is running low. '
            f'Current stock: {ingredient.current_stock} {ingredient.unit}. '
            f'Minimum required: {ingredient.minimum_stock} {ingredient.unit}.'
        ),
        priority  = 'HIGH',
        data      = {'ingredient_id': ingredient.id}
    )


def send_expired_alert(ingredient):
    """Notify managers when ingredient is expired"""
    notify_managers(
        branch    = ingredient.branch,
        type      = 'EXPIRED_ITEM',
        title     = f'Expired Item: {ingredient.name}',
        message   = (
            f'{ingredient.name} has expired. '
            f'Expiration date: {ingredient.expiration_date}. '
            f'Please remove it from stock immediately.'
        ),
        priority  = 'HIGH',
        data      = {'ingredient_id': ingredient.id}
    )


def send_reservation_reminder(reservation):
    """Remind managers of upcoming reservation"""
    notify_managers(
        branch    = reservation.branch,
        type      = 'RESERVATION',
        title     = f'Upcoming Reservation: {reservation.customer_name}',
        message   = (
            f'Reservation for {reservation.customer_name} is in 1 hour. '
            f'Table: {reservation.table}, '
            f'Party size: {reservation.guest_count}, '
            f'Time: {reservation.reservation_time}.'
        ),
        priority  = 'MEDIUM',
        data      = {'reservation_id': reservation.id}
    )


def send_maintenance_alert(schedule):
    """Notify managers of upcoming maintenance"""
    notify_managers(
        branch    = schedule.asset.branch,
        type      = 'MAINTENANCE',
        title     = f'Maintenance Due: {schedule.asset.name}',
        message   = (
            f'Maintenance scheduled for {schedule.asset.name} '
            f'is due on {schedule.next_due_date}. '
            f'Task: {schedule.title}.'
        ),
        priority  = 'MEDIUM',
        data      = {'schedule_id': schedule.id, 'asset_id': schedule.asset.id}
    )


def send_payroll_ready_alert(payroll):
    """Notify employee their payslip is ready"""
    notify_user(
        recipient = payroll.employee,
        branch    = payroll.employee.branch,
        type      = 'PAYROLL',
        title     = 'Your Payslip is Ready',
        message   = (
            f'Your payslip for {payroll.month}/{payroll.year} is ready. '
            f'Net salary: {payroll.net_salary}.'
        ),
        priority  = 'LOW',
        data      = {'payroll_id': payroll.id}
    )