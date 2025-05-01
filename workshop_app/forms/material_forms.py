from django import forms
from ..models import Material, MaterialEntry, MaterialType

class MaterialForm(forms.ModelForm):
    """Form for creating and updating materials"""
    class Meta:
        model = Material
        fields = [
            'material_id', 'serial_number', 'name', 'material_type', 
            'color', 'dimensions', 'unit_of_measurement',
            'supplier_name', 'brand_name',
            'minimum_stock_level', 'minimum_stock_alert', 'location_in_workshop',
            'expiration_date', 'project_association', 'notes'
        ]
        widgets = {
            'notes': forms.Textarea(attrs={'rows': 3}),
            'expiration_date': forms.DateInput(attrs={'type': 'date'}),
        }
    
    def clean_material_id(self):
        """Validate material ID format"""
        material_id = self.cleaned_data['material_id']
        
        # Check if it follows the expected format (e.g., PRT-PLA-0001)
        if not material_id or len(material_id.split('-')) != 3:
            raise forms.ValidationError(
                "Material ID must follow the format: CATEGORY-TYPE-NUMBER (e.g., PRT-PLA-0001)"
            )
        
        return material_id
    
    def __init__(self, *args, **kwargs):
        """Override init to set initial values and customize form"""
        super().__init__(*args, **kwargs)
        
        # Add help text
        self.fields['material_id'].help_text = "Format: CATEGORY-TYPE-NUMBER (e.g., PRT-PLA-0001)"
        self.fields['serial_number'].help_text = "Manufacturer's serial number or blank if none"
        
        # Make certain fields required
        self.fields['material_type'].required = True
        self.fields['unit_of_measurement'].required = True

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
