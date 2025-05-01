from django.db import models
from django.utils import timezone
from .material import Material

class MaterialEntry(models.Model):
    """Individual material purchase entries"""
    # Link to parent material
    material = models.ForeignKey(Material, on_delete=models.CASCADE, related_name='entries')
    
    # Purchase details
    quantity = models.DecimalField(max_digits=10, decimal_places=2, help_text="Amount added in material's unit of measurement")
    price_per_unit = models.DecimalField(max_digits=10, decimal_places=2, help_text="Purchase price for this entry")
    purchase_date = models.DateField(default=timezone.now)
    
    # Receipt and notes
    receipt = models.FileField(upload_to='receipts/materials/', blank=True, null=True, help_text="PDF receipt for this purchase")
    supplier_name = models.CharField(max_length=100, blank=True)
    notes = models.TextField(blank=True)
    
    # Audit information
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name_plural = "Material Entries"
        ordering = ['-purchase_date', '-created_at']
    
    def __str__(self):
        return f"Entry {self.id} for {self.material.material_id} - {self.quantity} {self.material.unit_of_measurement}"
    
    def save(self, *args, **kwargs):
        # Save the entry first
        super().save(*args, **kwargs)
        
        # Update the parent material's average price and stock
        self.material.update_price_and_stock()
