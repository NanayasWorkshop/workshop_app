from django import forms
from django.utils import timezone

from ..models import JobMaterial, Material

class JobMaterialForm(forms.ModelForm):
    """Form for adding material usage to a job"""
    
    class Meta:
        model = JobMaterial
        fields = ['material', 'quantity', 'unit_price', 'result', 'notes']
        widgets = {
            'notes': forms.Textarea(attrs={'rows': 2}),
        }
    
    def __init__(self, *args, **kwargs):
        self.job = kwargs.pop('job', None)
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Add help text
        self.fields['material'].help_text = "Select material used"
        self.fields['quantity'].help_text = "Amount used"
        self.fields['unit_price'].help_text = "Override unit price (optional)"
        self.fields['result'].help_text = "How the material was used"
        
        # Material queryset - only show materials with stock
        self.fields['material'].queryset = Material.objects.filter(current_stock__gt=0)
    
    def clean_quantity(self):
        """Validate that quantity is not more than available stock"""
        quantity = self.cleaned_data.get('quantity')
        material = self.cleaned_data.get('material')
        
        if not material:
            return quantity
            
        if quantity > material.current_stock:
            raise forms.ValidationError(
                f"Cannot use {quantity} {material.unit_of_measurement}. "
                f"Only {material.current_stock} available in stock."
            )
            
        return quantity
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        
        if self.job:
            instance.job = self.job
            
        # Set added_by from user
        if self.user:
            instance.added_by = self.user.get_full_name() or self.user.username
        
        # Set date_used to now
        instance.date_used = timezone.now()
        
        if commit:
            instance.save()
            
            # Update material stock
            if instance.result != 'returned':  # Don't reduce stock for returns
                material = instance.material
                material.current_stock -= instance.quantity
                material.save(update_fields=['current_stock'])
            
        return instance


class JobMaterialScanForm(forms.Form):
    """Form for adding materials to a job via scanning"""
    quantity = forms.DecimalField(max_digits=10, decimal_places=2, initial=1)
    result = forms.ChoiceField(choices=JobMaterial.RESULT_CHOICES, initial='success')
    notes = forms.CharField(widget=forms.Textarea(attrs={'rows': 2}), required=False)
    
    def __init__(self, *args, **kwargs):
        self.material = kwargs.pop('material', None)
        super().__init__(*args, **kwargs)
        
        # Customize form based on material
        if self.material:
            self.fields['quantity'].help_text = f"{self.material.unit_of_measurement} (max: {self.material.current_stock})"
            self.fields['quantity'].label = f"Quantity of {self.material.name}"
        
        # Add other help text
        self.fields['result'].help_text = "How the material was used"
