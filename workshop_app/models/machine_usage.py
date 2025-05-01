from django.db import models
from django.utils import timezone
from .machine import Machine

class MachineUsage(models.Model):
    """Track machine usage for specific jobs"""
    # Link to parent machine
    machine = models.ForeignKey(Machine, on_delete=models.CASCADE, related_name='usage_records')
    
    # Timing information
    start_time = models.DateTimeField(default=timezone.now)
    end_time = models.DateTimeField(null=True, blank=True)
    setup_time = models.IntegerField(help_text="Setup time in minutes", default=0)
    cleanup_time = models.IntegerField(help_text="Cleanup time in minutes", default=0)
    
    # Job information
    job_reference = models.CharField(max_length=100, blank=True, help_text="Reference to the job")
    operator_name = models.CharField(max_length=100, blank=True, help_text="Name of the machine operator")
    
    # Cost information
    operation_cost = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    setup_cost = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    cleanup_cost = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    total_cost = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    
    # Additional information
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-start_time']
        verbose_name_plural = "Machine Usage Records"
    
    def __str__(self):
        duration = self.get_duration_display()
        return f"{self.machine.name} used for {duration} on {self.start_time.strftime('%Y-%m-%d')}"
    
    def get_duration_minutes(self):
        """Calculate the operation duration in minutes"""
        if not self.end_time:
            return 0
            
        duration = self.end_time - self.start_time
        return int(duration.total_seconds() / 60)
    
    def get_duration_display(self):
        """Format the duration for display"""
        minutes = self.get_duration_minutes()
        hours, mins = divmod(minutes, 60)
        
        if hours > 0:
            return f"{hours}h {mins}m"
        else:
            return f"{mins}m"
    
    def get_total_time_minutes(self):
        """Get total time including setup and cleanup"""
        return self.get_duration_minutes() + self.setup_time + self.cleanup_time
    
    def calculate_costs(self):
        """Calculate costs based on machine rates and usage time"""
        if not self.end_time:
            return
            
        # Calculate operation cost
        operation_minutes = self.get_duration_minutes()
        operation_hours = operation_minutes / 60
        
        if self.machine.hourly_rate:
            self.operation_cost = self.machine.hourly_rate * operation_hours
        else:
            self.operation_cost = 0
            
        # Calculate setup cost
        if self.machine.setup_rate and self.setup_time > 0:
            setup_hours = self.setup_time / 60
            self.setup_cost = self.machine.setup_rate * setup_hours
        else:
            self.setup_cost = 0
            
        # Calculate cleanup cost
        if self.machine.cleanup_rate and self.cleanup_time > 0:
            cleanup_hours = self.cleanup_time / 60
            self.cleanup_cost = self.machine.cleanup_rate * cleanup_hours
        else:
            self.cleanup_cost = 0
            
        # Calculate total cost
        self.total_cost = (self.operation_cost or 0) + (self.setup_cost or 0) + (self.cleanup_cost or 0)
    
    def save(self, *args, **kwargs):
        """Override save to ensure costs are calculated"""
        self.calculate_costs()
        super().save(*args, **kwargs)
