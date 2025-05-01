from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Sum, Avg, Count
from django.utils import timezone

from ..models import Machine, MachineType, MachineUsage, MachineMaintenance, MachineConsumable
from ..forms import MachineForm, MachineUsageForm, MachineMaintenanceForm, MachineConsumableForm

@login_required
def machine_list(request):
    """
    Display a list of all machines in the workshop.
    """
    # Get filter parameters from request
    type_code = request.GET.get('type', '')
    search_query = request.GET.get('search', '')
    status_filter = request.GET.get('status', '')
    
    # Start with all machines
    machines = Machine.objects.all()
    
    # Apply filters if provided
    if type_code:
        machines = machines.filter(machine_type__code=type_code)
    
    if status_filter:
        machines = machines.filter(status=status_filter)
    
    if search_query:
        machines = machines.filter(
            Q(name__icontains=search_query) | 
            Q(machine_id__icontains=search_query) |
            Q(serial_number__icontains=search_query) |
            Q(manufacturer__icontains=search_query)
        )
    
    # Get all machine types for the filter dropdown
    machine_types = MachineType.objects.all()
    
    context = {
        'machines': machines,
        'machine_types': machine_types,
        'selected_type': type_code,
        'selected_status': status_filter,
        'search_query': search_query,
        'status_choices': Machine.STATUS_CHOICES,
    }
    
    return render(request, 'workshop_app/machines/list.html', context)

@login_required
def machine_detail(request, machine_id):
    """
    Display detailed information about a specific machine.
    """
    # Try to find by machine_id or serial_number
    machine = get_object_or_404(
        Machine, 
        Q(machine_id=machine_id) | Q(serial_number=machine_id)
    )
    
    # Get usage records
    usage_records = machine.usage_records.all().order_by('-start_time')[:10]
    
    # Get maintenance records
    maintenance_records = machine.maintenance_records.all().order_by('-maintenance_date')[:10]
    
    # Get consumables
    consumables = machine.consumables.all()
    
    # Calculate statistics
    total_usage_time = sum(record.get_duration_minutes() for record in usage_records if record.end_time)
    total_usage_hours = total_usage_time / 60 if total_usage_time else 0
    
    # Calculate costs
    total_maintenance_cost = machine.maintenance_records.aggregate(
        total=Sum('total_cost')
    )['total'] or 0
    
    total_usage_cost = machine.usage_records.aggregate(
        total=Sum('total_cost')
    )['total'] or 0
    
    context = {
        'machine': machine,
        'usage_records': usage_records,
        'maintenance_records': maintenance_records,
        'consumables': consumables,
        'total_usage_hours': total_usage_hours,
        'total_maintenance_cost': total_maintenance_cost,
        'total_usage_cost': total_usage_cost
    }
    
    return render(request, 'workshop_app/machines/detail.html', context)

@login_required
def machine_create(request):
    """
    Create a new machine.
    """
    if request.method == 'POST':
        form = MachineForm(request.POST)
        
        if form.is_valid():
            machine = form.save()
            messages.success(request, 'Machine created successfully.')
            return redirect('workshop_app:machine_detail', machine_id=machine.machine_id)
    else:
        form = MachineForm()
    
    context = {
        'form': form,
        'is_new': True,
        'title': 'Add New Machine',
    }
    
    return render(request, 'workshop_app/machines/form.html', context)

@login_required
def machine_update(request, machine_id):
    """
    Update an existing machine's information.
    """
    machine = get_object_or_404(Machine, machine_id=machine_id)
    
    if request.method == 'POST':
        form = MachineForm(request.POST, instance=machine)
        if form.is_valid():
            form.save()
            messages.success(request, 'Machine updated successfully.')
            return redirect('workshop_app:machine_detail', machine_id=machine.machine_id)
    else:
        form = MachineForm(instance=machine)
    
    context = {
        'form': form,
        'machine': machine,
        'is_new': False,
        'title': 'Edit Machine',
    }
    
    return render(request, 'workshop_app/machines/form.html', context)

@login_required
def machine_delete(request, machine_id):
    """
    Delete a machine.
    """
    machine = get_object_or_404(Machine, machine_id=machine_id)
    
    if request.method == 'POST':
        machine.delete()
        messages.success(request, 'Machine deleted successfully.')
        return redirect('workshop_app:machine_list')
    
    context = {
        'machine': machine,
    }
    
    return render(request, 'workshop_app/machines/confirm_delete.html', context)

@login_required
def machine_status_update(request, machine_id):
    """
    Update a machine's status.
    """
    machine = get_object_or_404(Machine, machine_id=machine_id)
    
    if request.method == 'POST':
        new_status = request.POST.get('status')
        
        if new_status in dict(Machine.STATUS_CHOICES):
            old_status = machine.status
            machine.status = new_status
            machine.save(update_fields=['status'])
            
            # If changing to maintenance, prompt for maintenance record creation
            if new_status == 'maintenance' and old_status != 'maintenance':
                messages.success(request, f'Machine status updated to {machine.get_status_display()}.')
                return redirect('workshop_app:machine_maintenance_add', machine_id=machine.machine_id)
            
            messages.success(request, f'Machine status updated to {machine.get_status_display()}.')
        else:
            messages.error(request, 'Invalid status selected.')
            
        return redirect('workshop_app:machine_detail', machine_id=machine.machine_id)
    
    context = {
        'machine': machine,
        'status_choices': Machine.STATUS_CHOICES,
    }
    
    return render(request, 'workshop_app/machines/status_form.html', context)

@login_required
def machine_usage_add(request, machine_id):
    """
    Record usage for a machine.
    """
    machine = get_object_or_404(Machine, machine_id=machine_id)
    
    if request.method == 'POST':
        form = MachineUsageForm(request.POST, machine=machine)
        if form.is_valid():
            usage = form.save()
            messages.success(request, 'Machine usage recorded successfully.')
            return redirect('workshop_app:machine_usage_success', usage_id=usage.id)
    else:
        # Pre-fill with current time
        initial = {
            'start_time': timezone.now(),
            'operator_name': request.user.get_full_name() if request.user.get_full_name() else request.user.username
        }
        form = MachineUsageForm(machine=machine, initial=initial)
    
    context = {
        'form': form,
        'machine': machine,
        'title': 'Record Machine Usage',
    }
    
    return render(request, 'workshop_app/machines/usage_form.html', context)

@login_required
def machine_usage_success(request, usage_id):
    """
    Show success page after recording machine usage.
    """
    usage = get_object_or_404(MachineUsage, id=usage_id)
    
    context = {
        'usage': usage,
        'machine': usage.machine,
        'title': 'Usage Recorded Successfully',
    }
    
    return render(request, 'workshop_app/machines/usage_success.html', context)

@login_required
def machine_maintenance_add(request, machine_id):
    """
    Record maintenance for a machine.
    """
    machine = get_object_or_404(Machine, machine_id=machine_id)
    
    if request.method == 'POST':
        form = MachineMaintenanceForm(request.POST, request.FILES, machine=machine)
        if form.is_valid():
            maintenance = form.save()
            
            # If this is corrective maintenance, update the machine status
            if maintenance.maintenance_type == 'corrective' and machine.status == 'maintenance':
                machine.status = 'active'
                machine.save(update_fields=['status'])
                messages.info(request, 'Machine status updated to Active.')
            
            messages.success(request, 'Machine maintenance recorded successfully.')
            return redirect('workshop_app:machine_detail', machine_id=machine.machine_id)
    else:
        # Pre-fill with current operator
        initial = {
            'performed_by': request.user.get_full_name() if request.user.get_full_name() else request.user.username
        }
        form = MachineMaintenanceForm(machine=machine, initial=initial)
    
    context = {
        'form': form,
        'machine': machine,
        'title': 'Record Machine Maintenance',
    }
    
    return render(request, 'workshop_app/machines/maintenance_form.html', context)

@login_required
def machine_consumable_add(request, machine_id):
    """
    Add a consumable to a machine.
    """
    machine = get_object_or_404(Machine, machine_id=machine_id)
    
    if request.method == 'POST':
        form = MachineConsumableForm(request.POST, machine=machine)
        if form.is_valid():
            consumable = form.save()
            messages.success(request, 'Consumable added successfully.')
            return redirect('workshop_app:machine_detail', machine_id=machine.machine_id)
    else:
        form = MachineConsumableForm(machine=machine)
    
    context = {
        'form': form,
        'machine': machine,
        'title': 'Add Machine Consumable',
    }
    
    return render(request, 'workshop_app/machines/consumable_form.html', context)
