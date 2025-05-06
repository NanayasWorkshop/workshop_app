from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from django.utils import timezone

from ..models import Job, JobMachine, Machine, StaffSettings
from ..forms import JobMachineForm, QuickMachineStartForm, QuickMachineEndForm

@login_required
def job_machine_add(request, job_id=None, machine_id=None):
    """
    Add machine usage to a job.
    If job_id is not provided, use the active job.
    """
    # Determine which job to use
    if job_id:
        job = get_object_or_404(Job, job_id=job_id)
    else:
        # Get active job from user settings
        try:
            staff_settings = StaffSettings.objects.get(user=request.user)
            job = staff_settings.active_job
            if not job:
                # Redirect to scanner to select a job
                messages.warning(request, "Please activate a job first.")
                return redirect('workshop_app:job_scanner_view')
        except StaffSettings.DoesNotExist:
            messages.warning(request, "Please activate a job first.")
            return redirect('workshop_app:job_scanner_view')
    
    # Get machine if provided
    machine = None
    if machine_id:
        machine = get_object_or_404(Machine, Q(machine_id=machine_id) | Q(serial_number=machine_id))
        
        # Check if machine is available
        if machine.status != 'active':
            messages.error(
                request, 
                f"Machine '{machine.name}' is currently {machine.get_status_display()} and cannot be used."
            )
            return redirect('workshop_app:job_detail', job_id=job.job_id)
    
    # Check for quick start workflow
    quick_start = request.GET.get('quick_start', 'false') == 'true'
    
    if quick_start and machine:
        # Handle quick start form
        if request.method == 'POST':
            form = QuickMachineStartForm(request.POST, machine=machine)
            if form.is_valid():
                # Create machine usage record
                machine_usage = JobMachine(
                    job=job,
                    machine=machine,
                    start_time=timezone.now(),
                    setup_time=form.cleaned_data.get('setup_time', 0) or 0,
                    operator_name=request.user.get_full_name() or request.user.username,
                    notes=form.cleaned_data.get('notes', ''),
                    is_active=True
                )
                
                # Set hourly rate from machine
                if machine.hourly_rate:
                    machine_usage.hourly_rate = machine.hourly_rate
                
                machine_usage.save()
                
                messages.success(
                    request, 
                    f"Started tracking usage of '{machine.name}' for job '{job.project_name}'"
                )
                
                # Redirect to job detail
                return redirect('workshop_app:job_detail', job_id=job.job_id)
        else:
            form = QuickMachineStartForm(machine=machine)
        
        context = {
            'form': form,
            'machine': machine,
            'job': job,
            'title': f"Start Using {machine.name}",
            'quick_start': True,
        }
        
        return render(request, 'workshop_app/jobs/machine_quick_start.html', context)
    
    # Handle machine selection or manual machine entry
    if request.method == 'POST' and not machine:
        # Check if the user is selecting a machine from a dropdown
        machine_id_from_form = request.POST.get('machine_selection', '')
        if machine_id_from_form:
            return redirect('workshop_app:job_machine_add_specific', job_id=job.job_id, machine_id=machine_id_from_form)
    
    # Standard machine usage form
    if request.method == 'POST':
        form = JobMachineForm(request.POST, job=job, user=request.user, machine=machine)
        if form.is_valid():
            machine_usage = form.save()
            
            # If end time is provided, calculate costs
            if machine_usage.end_time:
                machine_usage.calculate_costs()
                machine_usage.save()
                
                # Update job financial summary
                job.create_financial_summary()
                
                # Success message
                duration = machine_usage.get_duration_display()
                messages.success(
                    request, 
                    f"Added {duration} of machine '{machine_usage.machine.name}' to job"
                )
            else:
                # Starting machine usage
                messages.success(
                    request, 
                    f"Started tracking usage of '{machine_usage.machine.name}' for job"
                )
            
            # Redirect back to job detail
            return redirect('workshop_app:job_detail', job_id=job.job_id)
    else:
        # Pre-populate with defaults
        initial = {
            'start_time': timezone.now(),
            'operator_name': request.user.get_full_name() or request.user.username
        }
        
        # If machine is provided, set defaults
        if machine:
            initial['machine'] = machine
            if machine.hourly_rate:
                initial['hourly_rate'] = machine.hourly_rate
        
        form = JobMachineForm(job=job, user=request.user, machine=machine, initial=initial)
    
    # Get available machines for selection
    available_machines = Machine.objects.filter(status='active').order_by('name')
    
    context = {
        'form': form,
        'job': job,
        'machine': machine,
        'title': f"Add Machine Usage to {job.project_name}",
        'quick_start': False,
        'available_machines': available_machines
    }
    
    return render(request, 'workshop_app/jobs/machine_form.html', context)

@login_required
def job_machine_end(request, usage_id):
    """
    End an active machine usage session.
    """
    machine_usage = get_object_or_404(JobMachine, id=usage_id)
    
    # Check if already ended
    if not machine_usage.is_active or machine_usage.end_time:
        messages.warning(request, "This machine usage session has already ended.")
        return redirect('workshop_app:job_detail', job_id=machine_usage.job.job_id)
    
    if request.method == 'POST':
        form = QuickMachineEndForm(request.POST, machine_usage=machine_usage)
        if form.is_valid():
            # Update the machine usage record
            machine_usage.end_time = timezone.now()
            machine_usage.is_active = False
            
            # Add cleanup time
            cleanup_time = form.cleaned_data.get('cleanup_time', 0)
            if cleanup_time:
                machine_usage.cleanup_time = cleanup_time
            
            # Add notes
            additional_notes = form.cleaned_data.get('additional_notes', '')
            if additional_notes:
                if machine_usage.notes:
                    machine_usage.notes += f"\n\nEnd notes: {additional_notes}"
                else:
                    machine_usage.notes = additional_notes
            
            # Save and calculate costs
            machine_usage.calculate_costs()
            machine_usage.save()
            
            # Update job financial summary
            machine_usage.job.create_financial_summary()
            
            messages.success(
                request, 
                f"Ended machine usage of '{machine_usage.machine.name}'. "
                f"Total time: {machine_usage.get_duration_display()}"
            )
            
            return redirect('workshop_app:job_detail', job_id=machine_usage.job.job_id)
    else:
        form = QuickMachineEndForm(machine_usage=machine_usage)
    
    context = {
        'form': form,
        'machine_usage': machine_usage,
        'job': machine_usage.job,
        'machine': machine_usage.machine,
        'title': f"End Machine Usage",
    }
    
    return render(request, 'workshop_app/jobs/machine_end_form.html', context)

@login_required
def job_machine_list(request, job_id):
    """
    Show all machine usages for a specific job.
    """
    job = get_object_or_404(Job, job_id=job_id)
    
    # Get machine usages for this job
    machine_usages = JobMachine.objects.filter(job=job).order_by('-start_time')
    
    # Calculate totals
    total_duration_minutes = sum(
        [usage.get_duration_minutes() for usage in machine_usages if usage.end_time]
    )
    total_setup_minutes = sum([usage.setup_time for usage in machine_usages])
    total_cleanup_minutes = sum([usage.cleanup_time for usage in machine_usages])
    total_cost = sum([usage.total_cost or 0 for usage in machine_usages])
    
    # Check for active sessions
    active_sessions = machine_usages.filter(is_active=True)
    
    context = {
        'job': job,
        'machine_usages': machine_usages,
        'active_sessions': active_sessions,
        'total_duration_hours': total_duration_minutes / 60 if total_duration_minutes else 0,
        'total_setup_hours': total_setup_minutes / 60 if total_setup_minutes else 0,
        'total_cleanup_hours': total_cleanup_minutes / 60 if total_cleanup_minutes else 0,
        'total_cost': total_cost,
    }
    
    return render(request, 'workshop_app/jobs/machine_list.html', context)
