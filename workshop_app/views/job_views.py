from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Sum, Count
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.utils import timezone

from ..models import Job, JobStatus, JobMilestone, Client, ContactPerson
from ..models import JobMaterial, JobMachine, JobLabor, JobFinancial, StaffSettings
from ..forms import JobForm, JobMilestoneForm, JobStatusForm


@login_required
def job_list(request):
    """
    Display a list of all jobs with filtering options.
    """
    # Get filter parameters from request
    status_filter = request.GET.get('status', '')
    client_filter = request.GET.get('client', '')
    priority_filter = request.GET.get('priority', '')
    search_query = request.GET.get('search', '')
    show_completed = request.GET.get('show_completed', 'false') == 'true'
    
    # Start with all jobs, excluding personal jobs unless specifically requested
    jobs = Job.objects.filter(is_personal=False)
    
    # Apply filters if provided
    if status_filter:
        jobs = jobs.filter(status__name=status_filter)
    
    if client_filter:
        jobs = jobs.filter(client_id=client_filter)
    
    if priority_filter:
        jobs = jobs.filter(priority=priority_filter)
    
    if search_query:
        jobs = jobs.filter(
            Q(project_name__icontains=search_query) | 
            Q(job_id__icontains=search_query) |
            Q(client__name__icontains=search_query) |
            Q(description__icontains=search_query)
        )
    
    # Hide completed jobs unless requested
    if not show_completed:
        completed_statuses = JobStatus.objects.filter(
            name__in=['Completed', 'Complete', 'Finished', 'Done']
        ).values_list('id', flat=True)
        jobs = jobs.exclude(status__in=completed_statuses)
    
    # Get lists for filter dropdowns
    statuses = JobStatus.objects.all().order_by('order', 'name')
    clients = Client.objects.filter(status='active').order_by('name')
    
    # Get the active job for the current user
    try:
        staff_settings = StaffSettings.objects.get(user=request.user)
        active_job = staff_settings.active_job
    except StaffSettings.DoesNotExist:
        active_job = None
    
    context = {
        'jobs': jobs,
        'statuses': statuses,
        'clients': clients,
        'priority_choices': Job.PRIORITY_CHOICES,
        'selected_status': status_filter,
        'selected_client': client_filter,
        'selected_priority': priority_filter,
        'search_query': search_query,
        'show_completed': show_completed,
        'active_job': active_job,
    }
    
    return render(request, 'workshop_app/jobs/list.html', context)


@login_required
def job_detail(request, job_id):
    """
    Display detailed information about a specific job.
    """
    # Get the job
    job = get_object_or_404(Job, job_id=job_id)
    
    # Get job materials
    materials = JobMaterial.objects.filter(job=job).order_by('-date_used')
    
    # Get job machine usage
    machine_usages = JobMachine.objects.filter(job=job).order_by('-start_time')
    
    # Get job labor
    labor_entries = JobLabor.objects.filter(job=job).order_by('-date')
    
    # Get milestones
    milestones = JobMilestone.objects.filter(job=job).order_by('order')
    
    # Get financial summary
    try:
        financial = job.financial
    except JobFinancial.DoesNotExist:
        financial = JobFinancial.objects.create(job=job)
        job.create_financial_summary()
    
    # Check if this is the active job for the current user
    try:
        staff_settings = StaffSettings.objects.get(user=request.user)
        is_active_job = staff_settings.active_job == job
    except StaffSettings.DoesNotExist:
        is_active_job = False
    
    # Get all statuses for the status change form
    all_statuses = JobStatus.objects.all().order_by('order', 'name')
    
    context = {
        'job': job,
        'materials': materials,
        'machine_usages': machine_usages,
        'labor_entries': labor_entries,
        'milestones': milestones,
        'financial': financial,
        'is_active_job': is_active_job,
        'all_statuses': all_statuses,
    }
    
    return render(request, 'workshop_app/jobs/detail.html', context)


@login_required
def job_create(request):
    """
    Create a new job.
    """
    if request.method == 'POST':
        form = JobForm(request.POST, user=request.user)
        if form.is_valid():
            job = form.save()
            
            # Create financial record
            JobFinancial.objects.create(job=job)
            
            # Set as active job if checkbox checked
            if request.POST.get('set_active', '') == 'on':
                try:
                    staff_settings = StaffSettings.objects.get(user=request.user)
                except StaffSettings.DoesNotExist:
                    staff_settings = StaffSettings.objects.create(user=request.user)
                    
                staff_settings.set_active_job(job)
            
            messages.success(request, f"Job '{job.project_name}' created successfully.")
            return redirect('workshop_app:job_detail', job_id=job.job_id)
    else:
        # Preselect active client if provided
        initial = {}
        client_id = request.GET.get('client', '')
        if client_id:
            try:
                client = Client.objects.get(id=client_id)
                initial['client'] = client
            except Client.DoesNotExist:
                pass
        
        # Preselect default "In Progress" status
        try:
            status = JobStatus.objects.get(name='In Progress')
            initial['status'] = status
        except JobStatus.DoesNotExist:
            # If "In Progress" doesn't exist, get the first status
            status = JobStatus.objects.first()
            if status:
                initial['status'] = status
        
        form = JobForm(initial=initial, user=request.user)
    
    context = {
        'form': form,
        'title': 'Create New Job',
        'is_new': True,
    }
    
    return render(request, 'workshop_app/jobs/form.html', context)


@login_required
def job_update(request, job_id):
    """
    Update an existing job's information.
    """
    job = get_object_or_404(Job, job_id=job_id)
    
    if request.method == 'POST':
        form = JobForm(request.POST, instance=job, user=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, f"Job '{job.project_name}' updated successfully.")
            return redirect('workshop_app:job_detail', job_id=job.job_id)
    else:
        form = JobForm(instance=job, user=request.user)
    
    context = {
        'form': form,
        'job': job,
        'title': f"Edit Job: {job.project_name}",
        'is_new': False,
    }
    
    return render(request, 'workshop_app/jobs/form.html', context)


@login_required
def job_delete(request, job_id):
    """
    Delete a job and all related records.
    """
    job = get_object_or_404(Job, job_id=job_id)
    
    if request.method == 'POST':
        # Check if this is someone's active or personal job
        active_for = StaffSettings.objects.filter(active_job=job)
        personal_for = StaffSettings.objects.filter(personal_job=job)
        
        if active_for.exists() or personal_for.exists():
            messages.error(
                request, 
                "Cannot delete this job because it is currently active for one or more users."
            )
            return redirect('workshop_app:job_detail', job_id=job.job_id)
        
        # If it's safe to delete
        job_name = job.project_name
        job.delete()
        messages.success(request, f"Job '{job_name}' deleted successfully.")
        return redirect('workshop_app:job_list')
    
    context = {
        'job': job,
    }
    
    return render(request, 'workshop_app/jobs/confirm_delete.html', context)


@login_required
def job_status_change(request, job_id):
    """
    Change the status of a job.
    """
    job = get_object_or_404(Job, job_id=job_id)
    
    if request.method == 'POST':
        status_id = request.POST.get('status')
        if status_id:
            try:
                status = JobStatus.objects.get(id=status_id)
                old_status = job.status
                job.status = status
                
                # If moving to completed status, set end date
                complete_statuses = ['completed', 'complete', 'finished', 'done']
                if status.name.lower() in complete_statuses and not job.end_date:
                    job.end_date = timezone.now().date()
                
                job.save()
                
                # Create log entry
                from ..models import JobActivityLog
                JobActivityLog.objects.create(
                    user=request.user,
                    job=job,
                    activity_type='status_change',
                    description=f"Status changed from {old_status.name} to {status.name}"
                )
                
                messages.success(request, f"Job status updated to {status.name}.")
            except JobStatus.DoesNotExist:
                messages.error(request, "Invalid status selected.")
        else:
            messages.error(request, "No status selected.")
    
    return redirect('workshop_app:job_detail', job_id=job.job_id)


@login_required
def job_milestone_add(request, job_id):
    """
    Add a milestone to a job.
    """
    job = get_object_or_404(Job, job_id=job_id)
    
    if request.method == 'POST':
        form = JobMilestoneForm(request.POST, job=job)
        if form.is_valid():
            milestone = form.save()
            messages.success(request, f"Milestone '{milestone.name}' added successfully.")
            return redirect('workshop_app:job_detail', job_id=job.job_id)
    else:
        # Get the next order number
        next_order = JobMilestone.objects.filter(job=job).count() + 1
        form = JobMilestoneForm(job=job, initial={'order': next_order})
    
    context = {
        'form': form,
        'job': job,
        'title': f"Add Milestone to {job.project_name}",
    }
    
    return render(request, 'workshop_app/jobs/milestone_form.html', context)


@login_required
def job_milestone_update(request, milestone_id):
    """
    Update a job milestone.
    """
    milestone = get_object_or_404(JobMilestone, id=milestone_id)
    job = milestone.job
    
    if request.method == 'POST':
        form = JobMilestoneForm(request.POST, instance=milestone, job=job)
        if form.is_valid():
            form.save()
            messages.success(request, f"Milestone '{milestone.name}' updated successfully.")
            return redirect('workshop_app:job_detail', job_id=job.job_id)
    else:
        form = JobMilestoneForm(instance=milestone, job=job)
    
    context = {
        'form': form,
        'milestone': milestone,
        'job': job,
        'title': f"Edit Milestone: {milestone.name}",
    }
    
    return render(request, 'workshop_app/jobs/milestone_form.html', context)
