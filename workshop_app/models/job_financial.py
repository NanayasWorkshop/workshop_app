from django.db import models
from django.utils import timezone

from .job import Job

class JobFinancial(models.Model):
    """Financial tracking for jobs including costs and billing status"""
    
    # Core relationship
    job = models.OneToOneField(Job, on_delete=models.CASCADE, related_name='financial')
    
    # Cost breakdowns
    material_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    machine_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    labor_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    additional_costs = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    # Quote information
    quoted_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    variance = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    
    # Billing status
    BILLING_STATUS_CHOICES = [
        ('not_billed', 'Not Billed'),
        ('partially_billed', 'Partially Billed'),
        ('fully_billed', 'Fully Billed'),
        ('paid', 'Paid')
    ]
    billing_status = models.CharField(max_length=20, choices=BILLING_STATUS_CHOICES, default='not_billed')
    billed_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    invoice_reference = models.CharField(max_length=100, blank=True)
    
    # Tracking
    last_updated = models.DateTimeField(default=timezone.now)
    
    class Meta:
        verbose_name_plural = "Job Financials"
    
    def __str__(self):
        return f"Financials for {self.job.job_id}"
    
    def profit_margin(self):
        """Calculate profit margin if quoted"""
        if not self.quoted_amount or self.quoted_amount == 0:
            return None
        
        if not self.total_cost:
            return 100.0  # No costs, all profit
            
        profit = self.quoted_amount - self.total_cost
        return round((profit / self.quoted_amount) * 100, 2)
    
    def is_over_budget(self):
        """Check if job is over the quoted amount"""
        if not self.quoted_amount:
            return False
        return self.total_cost > self.quoted_amount
    
    def get_remaining_amount(self):
        """Calculate remaining amount to bill"""
        if not self.quoted_amount:
            return self.total_cost - self.billed_amount
        return self.quoted_amount - self.billed_amount
    
    def update_billing_status(self):
        """Update billing status based on billed amount"""
        if self.billed_amount <= 0:
            self.billing_status = 'not_billed'
        else:
            quoted = self.quoted_amount or self.total_cost
            
            if self.billed_amount >= quoted:
                self.billing_status = 'fully_billed'
            else:
                self.billing_status = 'partially_billed'
        
        self.save(update_fields=['billing_status'])
