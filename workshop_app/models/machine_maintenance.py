from django.db import models
from django.utils import timezone
from .machine import Machine

class MachineMaintenance(models.Model):
    """Track machine maintenance records"""
    # Link to parent machine
    machine = models.ForeignKey(Machine, on_delete=models.CASCADE, related_name='maintenance_records')
    
    # Maintenance information
    maintenance_date = models.DateField(default=timezone.now)
    
    MAINTENANCE_TYPE_CHOICES = [
        ('preventive', 'Preventive'),
        ('corrective', 'Corrective'),
        ('inspection', 'Inspection'),
        ('calibration', 'Calibration'),
        ('other', 'Other')
    ]
    maintenance_type = models.CharField(max_length=20, choices=MAINTENANCE_TYPE_CHOICES)
    
    # Who performed the maintenance
    performed_by = models.CharField(max_length=100, help_text="Person or company who performed maintenance")
    is_external_provider = models.BooleanField(default=False, help_text="Was maintenance done by external provider?")
    
    # Description of maintenance
    tasks_performed = models.TextField(help_text="Description of maintenance tasks performed")
    parts_replaced = models.TextField(blank=True, help_text="List of parts replaced during maintenance")
    
    # Cost information
    labor_cost = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    parts_cost = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    total_cost = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    
    # Additional information
    downtime_hours = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True, 
                                         help_text="Machine downtime in hours")
    result = models.TextField(blank=True, help_text="Result of the maintenance")
    issues_found = models.TextField(blank=True, help_text="Issues discovered during maintenance")
    
    # Documentation
    receipt = models.FileField(upload_to='receipts/maintenance/', blank=True, null=True)
    documentation = models.FileField(upload_to='docs/maintenance/', blank=True, null=True)
    
    # Tracking
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-maintenance_date', '-created_at']
        verbose_name_plural = "Machine Maintenance Records"
    
    def __str__(self):
        return f"{self.machine.name} - {self.get_maintenance_type_display()} on {self.maintenance_date}"
    
    def save(self, *args, **kwargs):
        """Override save to calculate total cost"""
        self.total_cost = (self.labor_cost or 0) + (self.parts_cost or 0)
        
        # After maintenance is completed, update machine status if needed
        super().save(*args, **kwargs)
        
        # If this is a corrective maintenance, we might want to update the machine status to active
        if self.maintenance_type == 'corrective' and self.machine.status == 'maintenance':
            self.machine.status = 'active'
            self.machine.save(update_fields=['status'])
