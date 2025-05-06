from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

from .job import Job

class StaffSettings(models.Model):
    """
    Stores settings for each staff member, including their active job
    """
    # Core relationship
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='settings')
    
    # Active job
    active_job = models.ForeignKey(Job, on_delete=models.SET_NULL, null=True, blank=True, 
                                  related_name='active_for_users')
    active_since = models.DateTimeField(null=True, blank=True)
    
    # Personal job for when not on a specific project
    personal_job = models.ForeignKey(Job, on_delete=models.SET_NULL, null=True, blank=True,
                                    related_name='+', help_text="User's personal job")
    
    # UI preferences
    show_active_job_banner = models.BooleanField(default=True)
    default_scan_for = models.CharField(max_length=10, default='job', 
                                      choices=[('job', 'Job'), ('material', 'Material'), ('machine', 'Machine')])

    # Last activity
    last_activity = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name_plural = "Staff Settings"
    
    def __str__(self):
        return f"Settings for {self.user.username}"
    
    def set_active_job(self, job):
        """Set a job as active for this user"""
        self.active_job = job
        self.active_since = timezone.now()
        self.save(update_fields=['active_job', 'active_since'])
        
        # Log job activation
        JobActivityLog.objects.create(
            user=self.user,
            job=job,
            activity_type='activation',
            description=f"Job activated by {self.user.get_full_name() or self.user.username}"
        )
    
    def clear_active_job(self):
        """Clear active job and revert to personal job"""
        if self.active_job:
            previous_job = self.active_job
            
            # Log job deactivation
            JobActivityLog.objects.create(
                user=self.user,
                job=previous_job,
                activity_type='deactivation',
                description=f"Job deactivated by {self.user.get_full_name() or self.user.username}"
            )
        
        # Set to personal job if available
        self.active_job = self.personal_job
        self.active_since = timezone.now() if self.personal_job else None
        self.save(update_fields=['active_job', 'active_since'])
    
    def ensure_personal_job(self):
        """Make sure user has a personal job"""
        if not self.personal_job:
            # Create a personal job for this user
            from .job import Job, JobStatus
            
            # Get or create 'Personal' status
            personal_status, _ = JobStatus.objects.get_or_create(
                name="Personal",
                defaults={
                    'description': "Personal job for tracking non-project work",
                    'color_code': "#6c757d",
                    'order': 999
                }
            )
            
            # Create personal job
            year = timezone.now().year
            username = self.user.username
            job = Job.objects.create(
                project_name=f"Personal Work - {self.user.get_full_name() or username}",
                client=None,  # No client for personal jobs
                status=personal_status,
                is_personal=True,
                owner=self.user,
                # Custom job ID for personal jobs: PERS-username-year
                job_id=f"PERS-{username[:4].upper()}-{year}"
            )
            
            # Set as personal job
            self.personal_job = job
            self.save(update_fields=['personal_job'])
            
            return job
            
        return self.personal_job


class JobActivityLog(models.Model):
    """
    Log of job activations, deactivations, and other activities
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='job_activities')
    job = models.ForeignKey(Job, on_delete=models.CASCADE, related_name='activities')
    timestamp = models.DateTimeField(default=timezone.now)
    
    ACTIVITY_TYPES = [
        ('activation', 'Job Activation'),
        ('deactivation', 'Job Deactivation'),
        ('material_usage', 'Material Usage'),
        ('machine_usage', 'Machine Usage'),
        ('status_change', 'Status Change'),
        ('other', 'Other Activity')
    ]
    activity_type = models.CharField(max_length=20, choices=ACTIVITY_TYPES)
    description = models.TextField()
    
    class Meta:
        ordering = ['-timestamp']
    
    def __str__(self):
        return f"{self.get_activity_type_display()} on {self.job.job_id} by {self.user.username}"
