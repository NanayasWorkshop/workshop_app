from django.db import models
from django.core.files.base import ContentFile
from django.contrib.auth.models import User
from django.utils import timezone
import qrcode
import io

from .client import Client, ContactPerson
# We'll import Quote when implemented

class JobStatus(models.Model):
    """Status options for jobs (customizable)"""
    name = models.CharField(max_length=50, unique=True)
    description = models.TextField(blank=True)
    color_code = models.CharField(max_length=7, default="#cccccc", help_text="Hex color code like #ff0000")
    order = models.IntegerField(default=0, help_text="Order for display")
    
    class Meta:
        ordering = ['order', 'name']
        verbose_name_plural = "Job Statuses"
    
    def __str__(self):
        return self.name

class Job(models.Model):
    """
    Main Job model for tracking projects.
    Can optionally be linked to a Quote.
    """
    # Basic Job Information
    job_id = models.CharField(max_length=15, unique=True)
    project_name = models.CharField(max_length=100)
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name='jobs')
    contact_person = models.ForeignKey(ContactPerson, on_delete=models.SET_NULL, null=True, blank=True)
    # original_quote = models.ForeignKey('Quote', on_delete=models.SET_NULL, null=True, blank=True)
    description = models.TextField(blank=True)
    created_date = models.DateTimeField(default=timezone.now)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_jobs')
    
    # Status Fields
    status = models.ForeignKey(JobStatus, on_delete=models.PROTECT, related_name='jobs')
    percent_complete = models.IntegerField(default=0, help_text="0-100")
    
    # Priority Options
    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('normal', 'Normal'),
        ('high', 'High'),
        ('urgent', 'Urgent')
    ]
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='normal')
    
    # Timeline Fields
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    deadline = models.DateField(null=True, blank=True)
    expected_completion = models.DateField(null=True, blank=True)
    
    # Special Job Types
    is_personal = models.BooleanField(default=False, help_text="Personal job for an operator")
    is_general = models.BooleanField(default=False, help_text="General workshop job")
    owner = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True, 
                              related_name='personal_jobs', help_text="Owner for personal jobs")
    
    # QR Code
    qr_code = models.ImageField(upload_to='qr_codes/jobs/', blank=True)
    
    class Meta:
        ordering = ['-created_date']
    
    def __str__(self):
        return f"{self.job_id} - {self.project_name}"
    
    def save(self, *args, **kwargs):
        # Auto-generate job_id if not provided
        if not self.job_id:
            # Get current year
            year = timezone.now().year
            
            # Find the highest job number for current year
            last_job = Job.objects.filter(
                job_id__startswith=f"JOB-{year}"
            ).order_by('-job_id').first()
            
            if last_job:
                # Extract the sequential number and increment
                try:
                    last_num = int(last_job.job_id.split('-')[-1])
                    next_num = last_num + 1
                except (ValueError, IndexError):
                    next_num = 1
            else:
                next_num = 1
                
            # Format: JOB-YYYY-XXXX
            self.job_id = f"JOB-{year}-{next_num:04d}"
            
        # Generate QR code for new jobs
        if not self.qr_code and self.job_id:
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=10,
                border=4,
            )
            qr.add_data(self.job_id)
            qr.make(fit=True)

            img = qr.make_image(fill_color="black", back_color="white")
            buffer = io.BytesIO()
            img.save(buffer)
            filename = f'qr_job_{self.job_id}.png'
            self.qr_code.save(filename, ContentFile(buffer.getvalue()), save=False)
        
        super().save(*args, **kwargs)
    
    def is_active(self):
        """Check if job is currently active"""
        active_statuses = ['in_progress', 'in progress', 'active']
        return self.status.name.lower() in active_statuses
    
    def is_complete(self):
        """Check if job is complete"""
        complete_statuses = ['completed', 'complete', 'finished', 'done']
        return self.status.name.lower() in complete_statuses
    
    def is_overdue(self):
        """Check if job is overdue"""
        if not self.deadline:
            return False
        return self.deadline < timezone.now().date() and not self.is_complete()
    
    def get_total_material_cost(self):
        """Calculate total material cost for this job"""
        from .job_material import JobMaterial
        material_costs = JobMaterial.objects.filter(job=self).aggregate(
            total=models.Sum(models.F('quantity') * models.F('unit_price'))
        )
        return material_costs['total'] or 0
    
    def get_total_machine_cost(self):
        """Calculate total machine cost for this job"""
        from .job_machine import JobMachine
        return JobMachine.objects.filter(job=self).aggregate(
            total=models.Sum('total_cost')
        )['total'] or 0
    
    def get_total_labor_cost(self):
        """Calculate total labor cost for this job"""
        from .job_labor import JobLabor
        return JobLabor.objects.filter(job=self).aggregate(
            total=models.Sum(models.F('hours') * models.F('hourly_rate'))
        )['total'] or 0
    
    def get_total_cost(self):
        """Calculate total cost for this job"""
        return (
            self.get_total_material_cost() + 
            self.get_total_machine_cost() + 
            self.get_total_labor_cost()
        )
    
    def create_financial_summary(self):
        """Update or create financial summary"""
        from .job_financial import JobFinancial
        
        summary, created = JobFinancial.objects.get_or_create(job=self)
        summary.material_cost = self.get_total_material_cost()
        summary.machine_cost = self.get_total_machine_cost()
        summary.labor_cost = self.get_total_labor_cost()
        summary.total_cost = summary.material_cost + summary.machine_cost + summary.labor_cost
        
        # If we have a quote, calculate variance
        # if self.original_quote:
        #     summary.quoted_amount = self.original_quote.total_amount
        #     summary.variance = summary.total_cost - summary.quoted_amount
        
        summary.last_updated = timezone.now()
        summary.save()
        
        return summary


class JobMilestone(models.Model):
    """Key milestones or phases in a job"""
    job = models.ForeignKey(Job, on_delete=models.CASCADE, related_name='milestones')
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    due_date = models.DateField(null=True, blank=True)
    completed = models.BooleanField(default=False)
    completed_date = models.DateField(null=True, blank=True)
    order = models.IntegerField(default=0)
    
    class Meta:
        ordering = ['order']
    
    def __str__(self):
        return f"{self.name} - {self.job.job_id}"
    
    def mark_complete(self):
        """Mark milestone as complete with current date"""
        self.completed = True
        self.completed_date = timezone.now().date()
        self.save()
