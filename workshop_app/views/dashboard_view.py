from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q, Sum, F

from ..models import (
    MaterialCategory, MaterialType, Material, 
    MachineType, Machine, Operator,
    MaterialTransaction, MachineUsage,
    Client, ContactPerson, Job, JobStatus,
    StaffSettings
)

@login_required
def dashboard_view(request):
    """
    Redesigned dashboard view that prioritizes workflow.
    Provides quick access to job scanning, material and machine usage tracking.
    """
    # Get active job for this user
    try:
        staff_settings = StaffSettings.objects.get(user=request.user)
        active_job = staff_settings.active_job
        
        if not active_job and not staff_settings.personal_job:
            # Ensure personal job exists
            personal_job = staff_settings.ensure_personal_job()
            # Set as active job
            staff_settings.set_active_job(personal_job)
            active_job = personal_job
            
    except StaffSettings.DoesNotExist:
        # Create settings for this user
        staff_settings = StaffSettings.objects.create(user=request.user)
        # Create personal job
        personal_job = staff_settings.ensure_personal_job()
        # Set as active job
        staff_settings.set_active_job(personal_job)
        active_job = personal_job
    
    # Recent jobs for this user (exclude personal jobs)
    recent_jobs = Job.objects.filter(
        is_personal=False
    ).order_by('-created_date')[:5]
    
    # Active jobs (in progress)
    in_progress_status = JobStatus.objects.filter(
        name__in=['In Progress', 'active', 'Active', 'in progress']
    ).values_list('id', flat=True)
    
    active_jobs = Job.objects.filter(
        status__in=in_progress_status,
        is_personal=False
    ).order_by('-created_date')[:5]
    
    # Material statistics (minimal info for dashboard)
    materials_count = Material.objects.count()
    low_stock_count = sum(1 for m in Material.objects.all() if m.is_low_stock())
    low_stock_materials = [m for m in Material.objects.all() if m.is_low_stock()][:5]  # Top 5 only
    
    # Machine statistics (minimal info for dashboard)
    machines_count = Machine.objects.count()
    active_machines = Machine.objects.filter(status='active').count()
    maintenance_machines = Machine.objects.filter(status='maintenance').count()
    
    # Recent material transactions
    recent_transactions = MaterialTransaction.objects.all().order_by('-transaction_date')[:5]
    
    # Recent machine usage
    recent_usages = MachineUsage.objects.all().order_by('-start_time')[:5]
    
    # Combine all stats
    stats = {
        'materials_count': materials_count,
        'low_stock_count': low_stock_count,
        'low_stock_materials': low_stock_materials,
        'machines_count': machines_count,
        'active_machines': active_machines,
        'maintenance_machines': maintenance_machines,
    }
    
    context = {
        'active_job': active_job,
        'recent_jobs': recent_jobs,
        'active_jobs': active_jobs,
        'stats': stats,
        'recent_transactions': recent_transactions,
        'recent_usages': recent_usages,
        'staff_settings': staff_settings,
    }
    
    return render(request, 'workshop_app/dashboard.html', context)
