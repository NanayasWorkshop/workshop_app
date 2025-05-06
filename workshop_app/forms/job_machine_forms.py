from django import forms
from django.utils import timezone

from ..models import JobMachine, Machine

class JobMachineForm(forms.ModelForm):
    """Form for adding machine usage to a job"""
    
    class Meta:
        model = JobMachine
        fields = [
            'machine', 'start_time', 'end_time', 
            'setup_time', 'cleanup_time', 
            'hourly_rate', 'operator_name', 'notes'
        ]
        widgets = {
            'start_time': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'end_time': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'notes': forms.Textarea(attrs={'rows': 2}),
        }
    
    def __init__(self, *args, **kwargs):
        self.job = kwargs.pop('job', None)
        self.user = kwargs.pop('user', None)
        self.machine = kwargs.pop('machine', None)
        super().__init__(*args, **kwargs)
        
        # Set initial values
        if self.user:
            self.fields['operator_name'].initial = self.user.get_full_name() or self.user.username
        
        # If machine is pre-selected, set and make read-only
        if self.machine:
            self.fields['machine'].initial = self.machine
            self.fields['machine'].widget.attrs['readonly'] = True
            self.fields['machine'].disabled = True
            
            # Set machine-specific rates
            if self.machine.hourly_rate:
                self.fields['hourly_rate'].initial = self.machine.hourly_rate
        
        # Add help text
        self.fields['start_time'].help_text = "When machine usage started"
        self.fields['end_time'].help_text = "When machine usage ended (leave blank for ongoing)"
        self.fields['setup_time'].help_text = "Time spent setting up (minutes)"
        self.fields['cleanup_time'].help_text = "Time spent cleaning up (minutes)"
    
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
        instance = super().save(commit=False)
        
        if self.job:
            instance.job = self.job
        
        # If machine is provided in form but disabled
        if self.machine and self.fields['machine'].disabled:
            instance.machine = self.machine
            
        # Calculate is_active based on end_time
        instance.is_active = not instance.end_time
            
        if commit:
            instance.save()
            
        return instance


class QuickMachineStartForm(forms.Form):
    """Form for quickly starting machine usage on a job"""
    setup_time = forms.IntegerField(initial=0, required=False, help_text="Setup time in minutes")
    notes = forms.CharField(widget=forms.Textarea(attrs={'rows': 2}), required=False)
    
    def __init__(self, *args, **kwargs):
        self.machine = kwargs.pop('machine', None)
        super().__init__(*args, **kwargs)
        
        # Customize form based on machine
        if self.machine:
            self.fields['setup_time'].label = f"Setup time for {self.machine.name}"
            
            # Use machine's default setup time if available
            if self.machine.setup_time:
                self.fields['setup_time'].initial = self.machine.setup_time


class QuickMachineEndForm(forms.Form):
    """Form for quickly ending machine usage on a job"""
    cleanup_time = forms.IntegerField(initial=0, required=False, help_text="Cleanup time in minutes")
    additional_notes = forms.CharField(widget=forms.Textarea(attrs={'rows': 2}), required=False)
    
    def __init__(self, *args, **kwargs):
        self.machine_usage = kwargs.pop('machine_usage', None)
        super().__init__(*args, **kwargs)
        
        # Customize form based on machine usage
        if self.machine_usage and self.machine_usage.machine:
            machine = self.machine_usage.machine
            self.fields['cleanup_time'].label = f"Cleanup time for {machine.name}"
            
            # Use machine's default cleanup time if available
            if machine.cleanup_time:
                self.fields['cleanup_time'].initial = machine.cleanup_time
