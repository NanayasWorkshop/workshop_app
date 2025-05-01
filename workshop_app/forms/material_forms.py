from django import forms
from ..models import Material, MaterialEntry, MaterialType

class MaterialForm(forms.ModelForm):
    """Form for creating and updating materials"""
    class Meta:
        model = Material
        fields = [
            'material_id', 'serial_number', 'supplier_sku', 'name', 'material_type', 
            'color', 'dimensions', 'unit_of_measurement',
            'supplier_name', 'brand_name',
            'minimum_stock_level', 'minimum_stock_alert', 'location_in_workshop',
            'expiration_date', 'project_association', 'notes'
        ]
        widgets = {
            'notes': forms.Textarea(attrs={'rows': 3}),
            'expiration_date': forms.DateInput(attrs={'type': 'date'}),
            'material_id': forms.TextInput(attrs={'readonly': 'readonly'}),
            'serial_number': forms.TextInput(attrs={'class': 'highlighted-field'}),
            'supplier_sku': forms.TextInput(attrs={'class': 'highlighted-field'}),
        }
    
    def __init__(self, *args, **kwargs):
        """Override init to set initial values and customize form"""
        super().__init__(*args, **kwargs)
        
        # Add help text
        self.fields['material_id'].help_text = "Auto-generated from material type and serial number"
        self.fields['serial_number'].help_text = "Manufacturer's serial number if available (important for tracking)"
        self.fields['supplier_sku'].help_text = "Supplier's SKU or product code (important for reordering)"
        
        # Make certain fields required
        self.fields['material_type'].required = True
        self.fields['unit_of_measurement'].required = True
        
        # Make material_id readonly for existing records, hide for new ones
        if self.instance.pk:
            self.fields['material_id'].widget.attrs['readonly'] = True
        else:
            self.fields['material_id'].required = False
            self.fields['material_id'].widget = forms.HiddenInput()

class MaterialEntryForm(forms.ModelForm):
    """Form for adding new material entries with receipt upload"""
    class Meta:
        model = MaterialEntry
        fields = [
            'quantity', 'price_per_unit', 'purchase_date',
            'receipt', 'supplier_name', 'notes'
        ]
        widgets = {
            'notes': forms.Textarea(attrs={'rows': 3}),
            'purchase_date': forms.DateInput(attrs={'type': 'date'}),
        }
    
    def __init__(self, *args, **kwargs):
        """Override init to set initial values"""
        self.material = kwargs.pop('material', None)
        super().__init__(*args, **kwargs)
        
        # Set help text for receipt
        self.fields['receipt'].help_text = "Upload PDF receipt (optional but recommended)"
        
        # If we have a material, set supplier name initial value
        if self.material and self.material.supplier_name:
            self.fields['supplier_name'].initial = self.material.supplier_name
    
    def save(self, commit=True):
        """Override save to add the material reference"""
        instance = super().save(commit=False)
        
        if self.material:
            instance.material = self.material
            
        if commit:
            instance.save()
            
        return instance
