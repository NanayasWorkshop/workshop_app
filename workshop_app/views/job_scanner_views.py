from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from django.utils import timezone

from ..models import Job, JobStatus, StaffSettings, JobActivityLog
from ..models import Material, Machine

@login_required
def job_scanner_view(request):
    """Main job scanner interface page"""
    
    # Get the active job for this user
    try:
        staff_settings = StaffSettings.objects.get(user=request.user)
        active_job = staff_settings.active_job
    except StaffSettings.DoesNotExist:
        # Create settings for this user if not exists
        staff_settings = StaffSettings.objects.create(user=request.user)
        active_job = None
        
        # Ensure personal job exists
        staff_settings.ensure_personal_job()
    
    # Get recent jobs for quick selection
    recent_jobs = Job.objects.filter(
        activities__user=request.user,
        is_personal=False
    ).distinct().order_by('-activities__timestamp')[:5]
    
    context = {
        'title': 'Job Scanner',
        'active_job': active_job,
        'recent_jobs': recent_jobs,
        'staff_settings': staff_settings,
    }
    
    return render(request, 'workshop_app/jobs/scanner.html', context)

@login_required
def job_lookup(request):
    """
    API endpoint to look up a job by ID
    Returns JSON with job details or error
    """
    identifier = request.GET.get('identifier', '')
    
    if not identifier:
        return JsonResponse({'error': 'No identifier provided'}, status=400)
    
    try:
        # Try to find by job_id
        job = Job.objects.get(job_id=identifier)
        
        # Return job details as JSON
        data = {
            'found': True,
            'job_id': job.job_id,
            'project_name': job.project_name,
            'client_name': job.client.name if job.client else 'No client',
            'status': job.status.name,
            'priority': job.get_priority_display(),
            'percent_complete': job.percent_complete,
            'detail_url': f"/jobs/{job.job_id}/",
            'activate_url': f"/jobs/{job.job_id}/activate/",
        }
        
        return JsonResponse(data)
        
    except Job.DoesNotExist:
        return JsonResponse({
            'found': False,
            'error': 'Job not found',
            'message': f'No job found with ID: {identifier}'
        }, status=404)
    
    except Exception as e:
        return JsonResponse({
            'found': False,
            'error': 'Error looking up job',
            'message': str(e)
        }, status=500)

@login_required
def job_activate(request, job_id):
    """
    Activate a job for the current user
    """
    job = get_object_or_404(Job, job_id=job_id)
    
    # Get or create StaffSettings for this user
    staff_settings, created = StaffSettings.objects.get_or_create(user=request.user)
    
    # Set the job as active
    staff_settings.set_active_job(job)
    
    # Create an activity log entry
    JobActivityLog.objects.create(
        user=request.user,
        job=job,
        activity_type='activation',
        description=f"Job activated by {request.user.get_full_name() or request.user.username}"
    )
    
    messages.success(request, f"Job '{job.project_name}' is now active. All scanned materials and machine usage will be associated with this job.")
    
    # Return to the previous page if available
    next_url = request.GET.get('next', '')
    if next_url:
        return redirect(next_url)
    
    # Default to job detail
    return redirect('workshop_app:job_detail', job_id=job.job_id)

@login_required
def job_deactivate(request):
    """
    Deactivate the current job and return to personal job
    """
    # Get StaffSettings for this user
    try:
        staff_settings = StaffSettings.objects.get(user=request.user)
    except StaffSettings.DoesNotExist:
        staff_settings = StaffSettings.objects.create(user=request.user)
    
    # Get current active job (for message)
    active_job = staff_settings.active_job
    
    # Ensure personal job exists
    personal_job = staff_settings.ensure_personal_job()
    
    # Clear active job (sets to personal job)
    staff_settings.clear_active_job()
    
    if active_job and active_job != personal_job:
        messages.success(request, f"Job '{active_job.project_name}' has been deactivated. You're now on your personal job.")
    else:
        messages.info(request, "Your personal job is now active.")
    
    # Return to the previous page if available
    next_url = request.GET.get('next', '')
    if next_url:
        return redirect(next_url)
    
    # Default to job list
    return redirect('workshop_app:job_list')
