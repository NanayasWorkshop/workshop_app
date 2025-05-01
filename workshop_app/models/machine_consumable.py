from django.db import models
from .machine import Machine

class MachineConsumable(models.Model):
    """Track consumable parts for machines"""
    # Link to parent machine
    machine = models.ForeignKey(Machine, on_delete=models.CASCADE, related_name='consumables')
    
    # Consumable information
    name = models.CharField(max_length=100, help_text="Name of the consumable part")
    description = models.TextField(blank=True)
    part_number = models.CharField(max_length=50, blank=True, help_text="Manufacturer's part number")
    
    # Stock information
    current_stock = models.IntegerField(default=0)
    minimum_stock_level = models.IntegerField(default=1)
    
    # Cost information
    cost_per_unit = models.DecimalField(max_digits=8, decimal_places=2)
    
    # Usage information
    expected_lifetime_hours = models.IntegerField(null=True, blank=True, 
                                                 help_text="Expected lifetime in machine operation hours")
    usage_count = models.IntegerField(default=0, help_text="Number of times this consumable has been replaced")
    
    # Supplier information
    supplier_name = models.CharField(max_length=100, blank=True)
    supplier_url = models.URLField(blank=True)
    
    # Tracking
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['machine', 'name']
    
    def __str__(self):
        return f"{self.name} for {self.machine.name}"
    
    def is_low_stock(self):
        """Check if the consumable is running low on stock"""
        return self.current_stock <= self.minimum_stock_level
    
    def get_cost_per_hour(self):
        """Calculate the cost per hour of operation"""
        if not self.expected_lifetime_hours or self.expected_lifetime_hours == 0:
            return 0
        
        return self.cost_per_unit / self.expected_lifetime_hours
    
    def record_replacement(self, quantity=1):
        """Record that this consumable has been replaced"""
        self.usage_count += quantity
        self.current_stock -= quantity
        self.save(update_fields=['usage_count', 'current_stock'])

class ConsumableReplacement(models.Model):
    """Track when consumables are replaced"""
    consumable = models.ForeignKey(MachineConsumable, on_delete=models.CASCADE, related_name='replacements')
    replacement_date = models.DateField(auto_now_add=True)
    quantity = models.IntegerField(default=1)
    machine_hours = models.IntegerField(null=True, blank=True, 
                                       help_text="Machine hours at time of replacement")
    replaced_by = models.CharField(max_length=100)
    notes = models.TextField(blank=True)
    
    def __str__(self):
        return f"{self.consumable.name} replaced on {self.replacement_date}"
    
    def save(self, *args, **kwargs):
        """Override save to update the consumable usage count"""
        super().save(*args, **kwargs)
        
        # Update the consumable usage count
        self.consumable.record_replacement(self.quantity)
