from django.db import models
from django.utils import timezone

from .job import Job
from .machine import Machine

class JobMachine(models.Model):
    """Track machine usage for a specific job"""
    
    # Core relationships
    job = models.ForeignKey(Job, on_delete=models.CASCADE, related_name='machine_usages')
    machine = models.ForeignKey(Machine, on_delete=models.CASCADE, related_name='job_usages')
    
    # Timing information
    start_time = models.DateTimeField(default=timezone.now)
    end_time = models.DateTimeField(null=True, blank=True)
    setup_time = models.IntegerField(default=0, help_text="Setup time in minutes")
    operation_time = models.IntegerField(default=0, help_text="Operation time in minutes")
    cleanup_time = models.IntegerField(default=0, help_text="Cleanup time in minutes")
    
    # Cost information
    hourly_rate = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    setup_cost = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    operation_cost = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    cleanup_cost = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    total_cost = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    
    # Additional information
    operator_name = models.CharField(max_length=100, blank=True)
    is_active = models.BooleanField(default=True, help_text="Whether this usage is ongoing")
    notes = models.TextField(blank=True)
    
    class Meta:
        ordering = ['-start_time']
        verbose_name_plural = "Job Machine Usages"
    
    def __str__(self):
        return f"{self.machine.name} - {self.get_duration_display()} - {self.job.job_id}"
    
    def get_duration_minutes(self):
        """Calculate the operation duration in minutes"""
        if not self.end_time:
            # If still active, calculate based on current time
            duration = timezone.now() - self.start_time
            return int(duration.total_seconds() / 60)
        else:
            # If ended, use recorded operation time or calculate from timestamps
            if self.operation_time > 0:
                return self.operation_time
            else:
                duration = self.end_time - self.start_time
                return int(duration.total_seconds() / 60)
    
    def get_total_time_minutes(self):
        """Get total time including setup and cleanup"""
        return self.get_duration_minutes() + self.setup_time + self.cleanup_time
    
    def get_duration_display(self):
        """Format the duration for display"""
        minutes = self.get_duration_minutes()
        hours, mins = divmod(minutes, 60)
        
        if hours > 0:
            return f"{hours}h {mins}m"
        else:
            return f"{mins}m"
    
    def calculate_costs(self):
        """Calculate all costs based on time and rates"""
        # Set hourly rate if not already set
        if not self.hourly_rate and self.machine.hourly_rate:
            self.hourly_rate = self.machine.hourly_rate
        
        # Calculate costs
        if self.hourly_rate:
            # Operation cost
            operation_minutes = self.get_duration_minutes()
            self.operation_time = operation_minutes  # Update the stored operation time
            operation_hours = operation_minutes / 60
            self.operation_cost = round(self.hourly_rate * operation_hours, 2)
            
            # Setup cost
            if self.setup_time > 0:
                setup_hours = self.setup_time / 60
                setup_rate = self.machine.setup_rate or self.hourly_rate
                self.setup_cost = round(setup_rate * setup_hours, 2)
            
            # Cleanup cost
            if self.cleanup_time > 0:
                cleanup_hours = self.cleanup_time / 60
                cleanup_rate = self.machine.cleanup_rate or self.hourly_rate
                self.cleanup_cost = round(cleanup_rate * cleanup_hours, 2)
            
            # Total cost
            self.total_cost = (
                (self.operation_cost or 0) + 
                (self.setup_cost or 0) + 
                (self.cleanup_cost or 0)
            )
    
    def end_usage(self):
        """End the current usage session"""
        if not self.end_time:
            self.end_time = timezone.now()
            self.is_active = False
            self.calculate_costs()
            self.save()
            
            # Update job's financial summary
            self.job.create_financial_summary()
    
    def save(self, *args, **kwargs):
        # Calculate costs before saving
        self.calculate_costs()
        
        # Set is_active based on end_time
        if self.end_time:
            self.is_active = False
        
        super().save(*args, **kwargs)
        
        # Update job's financial summary
        self.job.create_financial_summary()
