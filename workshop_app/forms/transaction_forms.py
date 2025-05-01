from django import forms
from ..models import MaterialTransaction

class MaterialTransactionForm(forms.ModelForm):
    """Form for recording material consumption or return"""
    
    class Meta:
        model = MaterialTransaction
        fields = ['quantity', 'job_reference', 'operator_name', 'notes']
        widgets = {
            'notes': forms.Textarea(attrs={'rows': 3}),
        }
    
    def __init__(self, *args, **kwargs):
        self.material = kwargs.pop('material', None)
        self.transaction_type = kwargs.pop('transaction_type', 'consumption')
        super().__init__(*args, **kwargs)
        
        # Set appropriate labels based on transaction type
        if self.transaction_type == 'consumption':
            self.fields['quantity'].label = "Quantity Used"
        else:
            self.fields['quantity'].label = "Quantity Returned"
        
        # Set help text
        self.fields['quantity'].help_text = f"Amount in {self.material.unit_of_measurement if self.material else 'units'}"
        
    def clean_quantity(self):
        """Validate quantity based on transaction type"""
        quantity = self.cleaned_data['quantity']
        
        # For consumption, check if there's enough stock
        if self.transaction_type == 'consumption' and self.material:
            if quantity > self.material.current_stock:
                raise forms.ValidationError(
                    f"Cannot use {quantity} {self.material.unit_of_measurement}. "
                    f"Only {self.material.current_stock} available."
                )
        
        # Ensure quantity is positive
        if quantity <= 0:
            raise forms.ValidationError("Quantity must be greater than zero.")
            
        return quantity
    
    def save(self, commit=True):
        """Override save to add the material and transaction type"""
        instance = super().save(commit=False)
        
        if self.material:
            instance.material = self.material
        
        instance.transaction_type = self.transaction_type
        
        if commit:
            instance.save()
            
        return instance

