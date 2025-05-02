from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from django.utils import timezone

from ..models import Machine, MachineUsage, MachineMaintenance, MachineConsumable, ConsumableReplacement

@login_required
def machine_scanner_view(request):
    """Main machine scanner interface page"""
    context = {
        'title': 'Machine Scanner',
    }
    return render(request, 'workshop_app/machines/scanner.html', context)

@login_required
def machine_lookup(request):
    """
    API endpoint to look up a machine by ID or serial number
    Returns JSON with machine details or error
    """
    identifier = request.GET.get('identifier', '')
    
    if not identifier:
        return JsonResponse({'error': 'No identifier provided'}, status=400)
    
    try:
        # Try to find by machine_id or serial_number
        machine = Machine.objects.get(
            Q(machine_id=identifier) | Q(serial_number=identifier)
        )
        
        # Return machine details as JSON
        data = {
            'found': True,
            'machine_id': machine.machine_id,
            'serial_number': machine.serial_number,
            'name': machine.name,
            'type': machine.machine_type.name,
            'status': machine.get_status_display(),
            'detail_url': f"/machines/{machine.machine_id}/",
            'usage_url': f"/machines/{machine.machine_id}/usage/add/",
            'maintenance_url': f"/machines/{machine.machine_id}/maintenance/add/",
        }
        
        return JsonResponse(data)
        
    except Machine.DoesNotExist:
        return JsonResponse({
            'found': False,
            'error': 'Machine not found',
            'message': f'No machine found with ID or serial number: {identifier}'
        }, status=404)
    
    except Exception as e:
        return JsonResponse({
            'found': False,
            'error': 'Error looking up machine',
            'message': str(e)
        }, status=500)

@login_required
def quick_usage_start(request, machine_id):
    """
    Quickly start a usage session for a machine
    """
    machine = get_object_or_404(Machine, Q(machine_id=machine_id) | Q(serial_number=machine_id))
    
    # Check if machine is available
    if machine.status != 'active':
        messages.error(request, f'Machine is currently {machine.get_status_display()} and cannot be used.')
        return redirect('workshop_app:machine_detail', machine_id=machine.machine_id)
    
    # Create a new usage record with start time
    usage = MachineUsage.objects.create(
        machine=machine,
        operator_name=request.user.get_full_name() if request.user.get_full_name() else request.user.username
    )
    
    messages.success(request, f'Started usage session for {machine.name}')
    
    # Store the usage ID in session for quick completion
    request.session['active_usage_id'] = usage.id
    
    return redirect('workshop_app:machine_usage_add', machine_id=machine.machine_id)

@login_required
def quick_usage_end(request, machine_id):
    """
    Quickly end an active usage session for a machine
    """
    # Get the active usage ID from session
    usage_id = request.session.get('active_usage_id')
    
    if not usage_id:
        messages.error(request, 'No active usage session found.')
        return redirect('workshop_app:machine_detail', machine_id=machine_id)
    
    try:
        usage = MachineUsage.objects.get(id=usage_id)
        
        # Check if this usage belongs to the machine
        if usage.machine.machine_id != machine_id and usage.machine.serial_number != machine_id:
            messages.error(request, 'Usage session does not match the scanned machine.')
            return redirect('workshop_app:machine_detail', machine_id=machine_id)
        
        # Set end time
        usage.end_time = timezone.now()
        usage.calculate_costs()
        usage.save()
        
        # Clear session
        if 'active_usage_id' in request.session:
            del request.session['active_usage_id']
        
        messages.success(request, f'Ended usage session for {usage.machine.name}')
        
        return redirect('workshop_app:machine_usage_success', usage_id=usage.id)
        
    except MachineUsage.DoesNotExist:
        messages.error(request, 'Usage session not found.')
        return redirect('workshop_app:machine_detail', machine_id=machine_id)

@login_required
def quick_maintenance_report(request, machine_id):
    """
    Quick maintenance reporting for a machine
    """
    machine = get_object_or_404(Machine, Q(machine_id=machine_id) | Q(serial_number=machine_id))
    
    if request.method == 'POST':
        # Simple form to just record the issue
        issue = request.POST.get('issue', '')
        
        if issue:
            # Create a maintenance record
            maintenance = MachineMaintenance.objects.create(
                machine=machine,
                maintenance_type='inspection',
                performed_by=request.user.get_full_name() if request.user.get_full_name() else request.user.username,
                tasks_performed='Issue inspection',
                issues_found=issue
            )
            
            # Update machine status if needed
            if machine.status == 'active':
                machine.status = 'maintenance'
                machine.save(update_fields=['status'])
                
            messages.success(request, 'Maintenance issue reported successfully.')
            return redirect('workshop_app:machine_detail', machine_id=machine.machine_id)
    
    context = {
        'machine': machine,
        'title': 'Report Maintenance Issue',
    }
    
    return render(request, 'workshop_app/machines/quick_maintenance_form.html', context)
