from celery import shared_task
from django.utils import timezone
from datetime import datetime, timedelta


@shared_task
def check_low_stock_all_branches():
    """
    Runs daily — checks all ingredients across all branches
    and sends low stock / expiry alerts
    """
    from inventory.models import Ingredient
    from .services import send_low_stock_alert, send_expired_alert

    ingredients = Ingredient.objects.filter(is_active=True)

    for ingredient in ingredients:
        if ingredient.is_low_stock:
            send_low_stock_alert(ingredient)
        if ingredient.is_expired:
            send_expired_alert(ingredient)

    return f"Checked {ingredients.count()} ingredients"


@shared_task
def send_reservation_reminders():
    """
    Runs every 15 minutes — sends reminders for
    reservations happening in the next hour
    """
    from pos.models import Reservation
    from .services import send_reservation_reminder

    now      = timezone.localtime()
    one_hour = now + timedelta(hours=1)

    # Reservation stores date + time separately, and the next hour may cross
    # midnight — narrow on the candidate dates in the DB, then combine
    # date+time into an aware datetime and check the precise window in Python.
    candidates = Reservation.objects.filter(
        reservation_date__in = [now.date(), one_hour.date()],
        status               = 'CONFIRMED',
    )

    sent = 0
    for reservation in candidates:
        when = datetime.combine(reservation.reservation_date, reservation.reservation_time)
        when = timezone.make_aware(when, now.tzinfo)
        if now <= when <= one_hour:
            send_reservation_reminder(reservation)
            sent += 1

    return f"Sent {sent} reservation reminders"


@shared_task
def check_maintenance_due():
    """
    Runs daily — checks maintenance schedules
    due in the next 3 days
    """
    from assets.models import MaintenanceSchedule
    from .services import send_maintenance_alert

    today    = timezone.now().date()
    deadline = today + timedelta(days=3)

    due_schedules = MaintenanceSchedule.objects.filter(
        next_due_date__lte = deadline,
        is_active          = True
    )

    for schedule in due_schedules:
        send_maintenance_alert(schedule)

    return f"Sent {due_schedules.count()} maintenance alerts"


@shared_task
def apply_monthly_depreciation_all():
    """
    Runs on 1st of every month — applies depreciation
    to all active assets across all branches
    """
    from assets.models import Asset
    from assets.services import apply_monthly_depreciation

    assets  = Asset.objects.filter(status='ACTIVE')
    count   = 0
    for asset in assets:
        record, _ = apply_monthly_depreciation(asset)
        if record:
            count += 1

    return f"Applied depreciation to {count} assets"