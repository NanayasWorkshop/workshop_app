from django import forms
from ..models import Machine, MachineType, MachineUsage, MachineMaintenance, MachineConsumable

class MachineForm(forms.ModelForm):
    """Form for creating and updating machines"""
    class Meta:
        model = Machine
        fields = [
            'machine_id', 'name', 'machine_type', 
            'manufacturer', 'model_number', 'serial_number',
            'location_in_workshop', 'supplier', 'purchase_date', 
            'purchase_price', 'warranty_end_date',
            'working_area', 'power_requirements', 'maximum_work_speed', 'precision',
            'hourly_rate', 'setup_time', 'setup_rate', 'cleanup_time', 'cleanup_rate',
            'status', 'notes'
        ]
        widgets = {
            'purchase_date': forms.DateInput(attrs={'type': 'date'}),
            'warranty_end_date': forms.DateInput(attrs={'type': 'date'}),
            'notes': forms.Textarea(attrs={'rows': 4, 'cols': 40}),
        }
    
    def clean_machine_id(self):
        """Validate machine ID format"""
        machine_id = self.cleaned_data['machine_id']
        
        # Check if it follows the expected format (e.g., FDM-001)
        if not machine_id or len(machine_id.split('-')) != 2:
            raise forms.ValidationError(
                "Machine ID must follow the format: TYPE-NUMBER (e.g., FDM-001)"
            )
        
        return machine_id
    
    def __init__(self, *args, **kwargs):
        """Override init to set initial values and customize form"""
        super().__init__(*args, **kwargs)
        
        # Add help text
        self.fields['machine_id'].help_text = "Format: TYPE-NUMBER (e.g., FDM-001)"
        self.fields['serial_number'].help_text = "Manufacturer's serial number"
        self.fields['notes'].help_text = "Additional notes about this machine (maintenance schedules, special requirements, etc.)"
        
        # Make certain fields required
        self.fields['machine_type'].required = True
        self.fields['name'].required = True

class MachineUsageForm(forms.ModelForm):
    """Form for recording machine usage"""
    
    class Meta:
        model = MachineUsage
        fields = [
            'start_time', 'end_time', 'setup_time', 'cleanup_time',
            'job_reference', 'operator_name', 'notes'
        ]
        widgets = {
            'start_time': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'end_time': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'notes': forms.Textarea(attrs={'rows': 3}),
        }
    
    def __init__(self, *args, **kwargs):
        """Override init to set initial values"""
        self.machine = kwargs.pop('machine', None)
        super().__init__(*args, **kwargs)
        
        # Set help text
        self.fields['setup_time'].help_text = "Time spent setting up the machine (in minutes)"
        self.fields['cleanup_time'].help_text = "Time spent cleaning up the machine (in minutes)"
    
    def clean(self):
        """Validate the form data"""
        cleaned_data = super().clean()
        start_time = cleaned_data.get('start_time')
        end_time = cleaned_data.get('end_time')
        
        # Ensure end time is after start time
        if start_time and end_time and end_time <= start_time:
            self.add_error('end_time', "End time must be after start time")
        
        return cleaned_data
    
    def save(self, commit=True):
        """Override save to add the machine reference"""
        instance = super().save(commit=False)
        
        if self.machine:
            instance.machine = self.machine
            
        if commit:
            instance.save()
            
        return instance

class MachineMaintenanceForm(forms.ModelForm):
    """Form for recording machine maintenance"""
    
    class Meta:
        model = MachineMaintenance
        fields = [
            'maintenance_date', 'maintenance_type', 'performed_by',
            'is_external_provider', 'tasks_performed', 'parts_replaced',
            'labor_cost', 'parts_cost', 'downtime_hours',
            'result', 'issues_found', 'receipt', 'documentation'
        ]
        widgets = {
            'maintenance_date': forms.DateInput(attrs={'type': 'date'}),
            'tasks_performed': forms.Textarea(attrs={'rows': 3}),
            'parts_replaced': forms.Textarea(attrs={'rows': 3}),
            'result': forms.Textarea(attrs={'rows': 3}),
            'issues_found': forms.Textarea(attrs={'rows': 3}),
        }
    
    def __init__(self, *args, **kwargs):
        """Override init to set initial values"""
        self.machine = kwargs.pop('machine', None)
        super().__init__(*args, **kwargs)
        
        # Set help text
        self.fields['receipt'].help_text = "Upload receipt for parts or external service (PDF)"
        self.fields['documentation'].help_text = "Upload any maintenance documentation (PDF)"
    
    def save(self, commit=True):
        """Override save to add the machine reference"""
        instance = super().save(commit=False)
        
        if self.machine:
            instance.machine = self.machine
            
        if commit:
            instance.save()
            
        return instance

class MachineConsumableForm(forms.ModelForm):
    """Form for adding and editing machine consumables"""
    
    class Meta:
        model = MachineConsumable
        fields = [
            'name', 'description', 'part_number',
            'current_stock', 'minimum_stock_level',
            'cost_per_unit', 'expected_lifetime_hours',
            'supplier_name', 'supplier_url'
        ]
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
        }
    
    def __init__(self, *args, **kwargs):
        """Override init to set initial values"""
        self.machine = kwargs.pop('machine', None)
        super().__init__(*args, **kwargs)
    
    def save(self, commit=True):
        """Override save to add the machine reference"""
        instance = super().save(commit=False)
        
        if self.machine:
            instance.machine = self.machine
            
        if commit:
            instance.save()
            
        return instance
