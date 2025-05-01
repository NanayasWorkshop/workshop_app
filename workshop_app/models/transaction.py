from django.db import models
from django.utils import timezone
from .material import Material

class MaterialTransaction(models.Model):
    """
    Model for tracking material consumption and returns without full entries
    """
    TRANSACTION_TYPES = [
        ('consumption', 'Consumption'),
        ('return', 'Return'),
    ]
    
    material = models.ForeignKey(Material, on_delete=models.CASCADE, related_name='transactions')
    quantity = models.DecimalField(max_digits=10, decimal_places=2, help_text="Amount used or returned")
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPES)
    transaction_date = models.DateTimeField(default=timezone.now)
    
    job_reference = models.CharField(max_length=100, blank=True, help_text="Optional job reference")
    operator_name = models.CharField(max_length=100, blank=True, help_text="Name of the person performing the transaction")
    notes = models.TextField(blank=True)
    
    class Meta:
        ordering = ['-transaction_date']
    
    def __str__(self):
        action = "used" if self.transaction_type == 'consumption' else "returned"
        return f"{self.quantity} {self.material.unit_of_measurement} {action} on {self.transaction_date.strftime('%Y-%m-%d %H:%M')}"
    
    def save(self, *args, **kwargs):
        """Override save to update the material stock"""
        super().save(*args, **kwargs)
        
        # Update material stock based on transaction type
        if self.transaction_type == 'consumption':
            # Reduce stock
            self.material.current_stock -= self.quantity
        else:
            # Add stock
            self.material.current_stock += self.quantity
        
        # Save material without triggering recalculation from entries
        Material.objects.filter(id=self.material.id).update(
            current_stock=self.material.current_stock
        )
