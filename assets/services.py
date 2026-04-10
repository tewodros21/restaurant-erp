from .models import Asset, DepreciationRecord
from django.utils import timezone


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

    depreciation_amount = asset.monthly_depreciation
    value_before        = asset.current_value
    value_after         = max(
        asset.current_value - depreciation_amount,
        asset.salvage_value  # never go below salvage value
    )

    # Update asset value
    asset.current_value = value_after
    asset.save()

    # Create depreciation record
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