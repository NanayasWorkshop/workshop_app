from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

from .job import Job
from .operator import Operator

class JobLabor(models.Model):
    """Track labor hours and costs for a specific job"""
    
    # Core relationships
    job = models.ForeignKey(Job, on_delete=models.CASCADE, related_name='labor_entries')
    operator = models.ForeignKey(User, on_delete=models.CASCADE, related_name='labor_entries')
    
    # Labor type and rates
    LABOR_TYPE_CHOICES = [
        ('design', 'Design'),
        ('production', 'Production'),
        ('assembly', 'Assembly'),
        ('quality_control', 'Quality Control'),
        ('packaging', 'Packaging'),
        ('other', 'Other')
    ]
    labor_type = models.CharField(max_length=20, choices=LABOR_TYPE_CHOICES)
    hourly_rate = models.DecimalField(max_digits=10, decimal_places=2)
    
    # Time tracking
    date = models.DateField(default=timezone.now)
    hours = models.DecimalField(max_digits=5, decimal_places=2, help_text="Hours worked")
    start_time = models.TimeField(null=True, blank=True)
    end_time = models.TimeField(null=True, blank=True)
    
    # Additional information
    description = models.TextField(blank=True)
    
    class Meta:
        ordering = ['-date']
        verbose_name_plural = "Job Labor Entries"
    
    def __str__(self):
        return f"{self.get_labor_type_display()} - {self.hours}h - {self.job.job_id}"
    
    def save(self, *args, **kwargs):
        # If operator has an Operator record, use that hourly rate if not set
        if not self.hourly_rate:
            try:
                operator_record = Operator.objects.get(user=self.operator)
                self.hourly_rate = operator_record.hourly_rate
            except Operator.DoesNotExist:
                # Default rate if no operator record
                self.hourly_rate = 50.00
        
        # If start_time and end_time are set, calculate hours
        if self.start_time and self.end_time and not self.hours:
            # Convert to datetime for calculation
            start_dt = timezone.datetime.combine(self.date, self.start_time)
            end_dt = timezone.datetime.combine(self.date, self.end_time)
            
            # If end time is before start time, assume it's the next day
            if end_dt < start_dt:
                end_dt = end_dt + timezone.timedelta(days=1)
            
            # Calculate duration in hours
            duration = end_dt - start_dt
            self.hours = round(duration.total_seconds() / 3600, 2)
        
        super().save(*args, **kwargs)
        
        # Update job's financial summary
        self.job.create_financial_summary()
    
    def get_cost(self):
        """Calculate the cost for this labor entry"""
        return self.hours * self.hourly_rate
