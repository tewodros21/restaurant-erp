from .models import Asset, DepreciationRecord
from django.utils import timezone
from django.db import transaction


def apply_monthly_depreciation(asset):
    """
    Calculate and apply monthly depreciation for an asset.
    Called by a scheduled task (Celery) at end of each month.
    """
    now   = timezone.now()
    month = now.month
    year  = now.year

    # Skip if already processed this month
    already_done = DepreciationRecord.objects.filter(
        asset=asset, month=month, year=year
    ).exists()

    if already_done:
        return None, "Depreciation already applied this month"

    # Skip if asset is retired or disposed
    if asset.status in ['RETIRED', 'DISPOSED']:
        return None, "Asset is not active"

    # Skip if current value already at salvage value
    if asset.current_value <= asset.salvage_value:
        return None, "Asset fully depreciated"

    value_before = asset.current_value
    value_after  = max(
        asset.current_value - asset.monthly_depreciation,
        asset.salvage_value  # never go below salvage value
    )
    # Record the amount actually written off (the clamp above may reduce it),
    # so value_before - depreciation_amount == value_after always holds.
    depreciation_amount = value_before - value_after

    # Value update and record creation must commit together, else a crash
    # between them reduces the value with no record — and the idempotency
    # guard above would then skip this asset forever.
    with transaction.atomic():
        asset.current_value = value_after
        asset.save(update_fields=['current_value', 'updated_at'])

        record = DepreciationRecord.objects.create(
            asset               = asset,
            month               = month,
            year                = year,
            depreciation_amount = depreciation_amount,
            value_before        = value_before,
            value_after         = value_after
        )

    return record, "Depreciation applied successfully"


def apply_depreciation_all_assets(branch):
    """Apply depreciation to all active assets in a branch"""
    assets  = Asset.objects.filter(branch=branch, status='ACTIVE')
    results = []
    for asset in assets:
        record, message = apply_monthly_depreciation(asset)
        results.append({
            'asset':   asset.name,
            'message': message,
            'record':  record
        })
    return results


def record_maintenance(log):
    """Advance a maintenance schedule's next due date after a completed log.

    Without this the schedule's next_due_date never moves, so every alert task
    re-flags the same schedule as 'due' forever.
    """
    schedule = log.schedule
    if not schedule or log.status != 'COMPLETED':
        return

    if log.next_due_date:
        schedule.next_due_date = log.next_due_date
    else:
        from datetime import timedelta
        freq_days = {'WEEKLY': 7, 'MONTHLY': 30, 'QUARTERLY': 91, 'YEARLY': 365}
        base = log.performed_at.date() if log.performed_at else timezone.localdate()
        schedule.next_due_date = base + timedelta(days=freq_days.get(schedule.frequency, 30))

    schedule.save(update_fields=['next_due_date'])


def get_upcoming_maintenance(branch, days=7):
    """Get maintenance schedules due within the next N days"""
    from datetime import timedelta
    from .models import MaintenanceSchedule
    today    = timezone.now().date()
    deadline = today + timedelta(days=days)
    return MaintenanceSchedule.objects.filter(
        asset__branch  = branch,
        next_due_date__lte = deadline,
        is_active      = True
    ).order_by('next_due_date')