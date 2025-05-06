from django import forms
from django.contrib.auth.models import User
from django.utils import timezone

from ..models import JobLabor, Operator

class JobLaborForm(forms.ModelForm):
    """Form for adding labor time to a job"""
    
    class Meta:
        model = JobLabor
        fields = [
            'operator', 'labor_type', 'date', 
            'hours', 'start_time', 'end_time',
            'hourly_rate', 'description'
        ]
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
            'start_time': forms.TimeInput(attrs={'type': 'time'}),
            'end_time': forms.TimeInput(attrs={'type': 'time'}),
            'description': forms.Textarea(attrs={'rows': 2}),
        }
    
    def __init__(self, *args, **kwargs):
        self.job = kwargs.pop('job', None)
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Set initial values
        if self.user:
            self.fields['operator'].initial = self.user
            
            # Try to get hourly rate from operator profile
            try:
                operator = Operator.objects.get(user=self.user)
                self.fields['hourly_rate'].initial = operator.hourly_rate
            except Operator.DoesNotExist:
                pass
        
        # Default date to today
        self.fields['date'].initial = timezone.now().date()
        
        # Add help text
        self.fields['labor_type'].help_text = "Type of work performed"
        self.fields['hours'].help_text = "Hours worked (can be decimal, e.g., 1.5)"
        self.fields['start_time'].help_text = "If tracking by time instead of hours"
        self.fields['end_time'].help_text = "If tracking by time instead of hours"
    
    def clean(self):
        """Validate the form data"""
        cleaned_data = super().clean()
        hours = cleaned_data.get('hours')
        start_time = cleaned_data.get('start_time')
        end_time = cleaned_data.get('end_time')
        
        # Ensure either hours OR start/end time is provided
        if not hours and not (start_time and end_time):
            self.add_error(
                'hours', 
                "Either enter hours directly or provide both start and end times"
            )
        
        # If both are provided, start/end time takes precedence
        
        return cleaned_data
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        
        if self.job:
            instance.job = self.job
            
        if commit:
            instance.save()
            
        return instance


class QuickLaborForm(forms.Form):
    """Form for quick labor time tracking on a job"""
    LABOR_TYPE_CHOICES = JobLabor.LABOR_TYPE_CHOICES
    
    labor_type = forms.ChoiceField(choices=LABOR_TYPE_CHOICES)
    hours = forms.DecimalField(max_digits=5, decimal_places=2)
    description = forms.CharField(widget=forms.Textarea(attrs={'rows': 2}), required=False)
    
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Add help text
        self.fields['labor_type'].help_text = "Type of work performed"
        self.fields['hours'].help_text = "Hours worked"
        self.fields['description'].help_text = "Brief description of work done"
