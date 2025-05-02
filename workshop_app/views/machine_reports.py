from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Avg, Count, F, Q, ExpressionWrapper, fields
from django.db.models.functions import TruncDate, TruncMonth, TruncWeek
from django.utils import timezone
import datetime

from ..models import Machine, MachineUsage, MachineMaintenance, MachineType

@login_required
def machine_usage_list(request):
    """
    Display a list of all machine usage records.
    """
    # Get filter parameters from request
    machine_id = request.GET.get('machine', '')
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')
    operator = request.GET.get('operator', '')
    status = request.GET.get('status', '')
    
    # Start with all usage records
    usages = MachineUsage.objects.all().select_related('machine').order_by('-start_time')
    
    # Apply filters if provided
    if machine_id:
        usages = usages.filter(machine__machine_id=machine_id)
    
    if date_from:
        try:
            date_from = datetime.datetime.strptime(date_from, '%Y-%m-%d').date()
            usages = usages.filter(start_time__date__gte=date_from)
        except ValueError:
            pass
    
    if date_to:
        try:
            date_to = datetime.datetime.strptime(date_to, '%Y-%m-%d').date()
            usages = usages.filter(start_time__date__lte=date_to)
        except ValueError:
            pass
    
    if operator:
        usages = usages.filter(operator_name__icontains=operator)
    
    if status == 'active':
        usages = usages.filter(end_time__isnull=True)
    elif status == 'completed':
        usages = usages.filter(end_time__isnull=False)
    
    # Get all machines for the filter dropdown
    machines = Machine.objects.all().order_by('machine_id')
    
    # Calculate totals
    total_cost = usages.aggregate(total=Sum('total_cost'))['total'] or 0
    total_machine_time = 0
    total_setup_time = 0
    total_cleanup_time = 0
    
    for usage in usages:
        if usage.get_duration_minutes():
            total_machine_time += usage.get_duration_minutes()
        if usage.setup_time:
            total_setup_time += usage.setup_time
        if usage.cleanup_time:
            total_cleanup_time += usage.cleanup_time
    
    # For active sessions, add a current duration
    now = timezone.now()
    
    context = {
        'usages': usages,
        'machines': machines,
        'selected_machine': machine_id,
        'date_from': date_from,
        'date_to': date_to,
        'operator_filter': operator,
        'status_filter': status,
        'total_cost': total_cost,
        'total_machine_time': total_machine_time / 60 if total_machine_time > 0 else 0,  # Convert to hours
        'total_setup_time': total_setup_time / 60 if total_setup_time > 0 else 0,  # Convert to hours
        'total_cleanup_time': total_cleanup_time / 60 if total_cleanup_time > 0 else 0,  # Convert to hours
        'current_time': now,
    }
    
    return render(request, 'workshop_app/machines/machine_usage_list.html', context)

@login_required
def maintenance_list(request):
    """
    Display a list of all machine maintenance records.
    """
    # Get filter parameters from request
    machine_id = request.GET.get('machine', '')
    maintenance_type = request.GET.get('type', '')
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')
    
    # Start with all maintenance records
    records = MachineMaintenance.objects.all().select_related('machine').order_by('-maintenance_date')
    
    # Apply filters if provided
    if machine_id:
        records = records.filter(machine__machine_id=machine_id)
    
    if maintenance_type:
        records = records.filter(maintenance_type=maintenance_type)
    
    if date_from:
        try:
            date_from = datetime.datetime.strptime(date_from, '%Y-%m-%d').date()
            records = records.filter(maintenance_date__gte=date_from)
        except ValueError:
            pass
    
    if date_to:
        try:
            date_to = datetime.datetime.strptime(date_to, '%Y-%m-%d').date()
            records = records.filter(maintenance_date__lte=date_to)
        except ValueError:
            pass
    
    # Get all machines for the filter dropdown
    machines = Machine.objects.all().order_by('machine_id')
    
    # Calculate totals
    total_cost = records.aggregate(total=Sum('total_cost'))['total'] or 0
    total_downtime = records.aggregate(total=Sum('downtime_hours'))['total'] or 0
    
    context = {
        'records': records,
        'machines': machines,
        'selected_machine': machine_id,
        'selected_type': maintenance_type,
        'date_from': date_from,
        'date_to': date_to,
        'maintenance_types': MachineMaintenance.MAINTENANCE_TYPE_CHOICES,
        'total_cost': total_cost,
        'total_downtime': total_downtime,
    }
    
    return render(request, 'workshop_app/machines/maintenance_list.html', context)

@login_required
def machine_usage_report(request):
    """
    Generate a report on machine usage patterns.
    """
    # Get filter parameters
    period = request.GET.get('period', 'month')  # day, week, month
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')
    machine_type = request.GET.get('machine_type', '')
    
    # Default date range - last 3 months
    if not date_from:
        date_from = (timezone.now() - datetime.timedelta(days=90)).date()
    else:
        try:
            date_from = datetime.datetime.strptime(date_from, '%Y-%m-%d').date()
        except ValueError:
            date_from = (timezone.now() - datetime.timedelta(days=90)).date()
    
    if not date_to:
        date_to = timezone.now().date()
    else:
        try:
            date_to = datetime.datetime.strptime(date_to, '%Y-%m-%d').date()
        except ValueError:
            date_to = timezone.now().date()
    
    # Filter usage records
    usages = MachineUsage.objects.filter(
        start_time__date__gte=date_from,
        start_time__date__lte=date_to
    ).select_related('machine', 'machine__machine_type')
    
    if machine_type:
        usages = usages.filter(machine__machine_type__code=machine_type)
    
    # Group by machine type
    machine_type_stats = {}
    for usage in usages:
        type_code = usage.machine.machine_type.code
        if type_code not in machine_type_stats:
            machine_type_stats[type_code] = {
                'name': usage.machine.machine_type.name,
                'total_hours': 0,
                'total_cost': 0,
                'count': 0
            }
        
        # Add duration if completed
        if usage.end_time:
            hours = usage.get_duration_minutes() / 60
            machine_type_stats[type_code]['total_hours'] += hours
            machine_type_stats[type_code]['count'] += 1
            if usage.total_cost:
                machine_type_stats[type_code]['total_cost'] += float(usage.total_cost)
    
    # Get machine types for filter
    machine_types = MachineType.objects.all().order_by('code')
    
    # Calculate most used machines
    machine_usage_stats = {}
    for usage in usages:
        machine_id = usage.machine.machine_id
        if machine_id not in machine_usage_stats:
            machine_usage_stats[machine_id] = {
                'name': usage.machine.name,
                'total_hours': 0,
                'total_cost': 0,
                'count': 0
            }
        
        # Add duration if completed
        if usage.end_time:
            hours = usage.get_duration_minutes() / 60
            machine_usage_stats[machine_id]['total_hours'] += hours
            machine_usage_stats[machine_id]['count'] += 1
            if usage.total_cost:
                machine_usage_stats[machine_id]['total_cost'] += float(usage.total_cost)
    
    # Sort by total hours
    top_machines = sorted(
        machine_usage_stats.items(), 
        key=lambda x: x[1]['total_hours'], 
        reverse=True
    )[:10]
    
    context = {
        'period': period,
        'date_from': date_from,
        'date_to': date_to,
        'machine_types': machine_types,
        'selected_machine_type': machine_type,
        'machine_type_stats': machine_type_stats,
        'top_machines': top_machines,
        'total_usage_count': usages.count(),
    }
    
    return render(request, 'workshop_app/machines/usage_report.html', context)
