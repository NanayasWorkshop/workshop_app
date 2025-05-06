from django.db import models
from django.utils import timezone

from .job import Job
from .material import Material

class JobMaterial(models.Model):
    """Track materials used for a specific job"""
    
    # Core relationships
    job = models.ForeignKey(Job, on_delete=models.CASCADE, related_name='materials')
    material = models.ForeignKey(Material, on_delete=models.CASCADE, related_name='job_usages')
    
    # Usage details
    quantity = models.DecimalField(max_digits=10, decimal_places=2)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    date_used = models.DateTimeField(default=timezone.now)
    added_by = models.CharField(max_length=100, blank=True)
    
    # Status of material
    RESULT_CHOICES = [
        ('success', 'Successful'),
        ('scrap', 'Scrap/Waste'),
        ('failed', 'Failed'),
        ('returned', 'Returned to Inventory')
    ]
    result = models.CharField(max_length=20, choices=RESULT_CHOICES, default='success')
    
    # Notes
    notes = models.TextField(blank=True)
    
    class Meta:
        ordering = ['-date_used']
        verbose_name_plural = "Job Materials"
    
    def __str__(self):
        return f"{self.material.name} ({self.quantity} {self.material.unit_of_measurement}) - {self.job.job_id}"
    
    def save(self, *args, **kwargs):
        # If unit_price not provided, get from material
        if not self.unit_price and self.material.price_per_unit:
            self.unit_price = self.material.price_per_unit
            
        super().save(*args, **kwargs)
        
        # Update job's financial summary
        self.job.create_financial_summary()
    
    def get_total_price(self):
        """Calculate total price for this material usage"""
        if self.unit_price:
            return self.quantity * self.unit_price
        return None
    
    def return_to_inventory(self, quantity=None):
        """Return material to inventory"""
        if quantity is None:
            quantity = self.quantity
            
        if quantity > self.quantity:
            quantity = self.quantity
            
        if quantity <= 0:
            return
            
        # Update material inventory
        self.material.current_stock += quantity
        self.material.save(update_fields=['current_stock'])
        
        # Update this record
        self.quantity -= quantity
        self.result = 'returned'
        self.save()
