from django import forms
from django.contrib.auth.models import User
from django.utils import timezone

from ..models import Job, JobStatus, JobMilestone, Client, ContactPerson

class JobForm(forms.ModelForm):
    """Form for creating and updating jobs"""
    
    class Meta:
        model = Job
        fields = [
            'project_name', 'client', 'contact_person', 
            'description', 'status', 'priority',
            'deadline', 'start_date', 'expected_completion'
        ]
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
            'deadline': forms.DateInput(attrs={'type': 'date'}),
            'start_date': forms.DateInput(attrs={'type': 'date'}),
            'expected_completion': forms.DateInput(attrs={'type': 'date'}),
        }
    
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Add fieldsets
        self.fieldsets = [
            ('Basic Information', ['project_name', 'client', 'contact_person', 'description']),
            ('Status Information', ['status', 'priority']),
            ('Timeline', ['deadline', 'start_date', 'expected_completion']),
        ]
        
        # Filter contact persons based on selected client
        if 'client' in self.data:
            try:
                client_id = int(self.data.get('client'))
                self.fields['contact_person'].queryset = ContactPerson.objects.filter(client_id=client_id)
            except (ValueError, TypeError):
                self.fields['contact_person'].queryset = ContactPerson.objects.none()
        elif self.instance.pk and self.instance.client:
            self.fields['contact_person'].queryset = self.instance.client.contacts.all()
        else:
            self.fields['contact_person'].queryset = ContactPerson.objects.none()
        
        # Add help text
        self.fields['project_name'].help_text = "Name or title for this project"
        self.fields['contact_person'].help_text = "Client contact for this job"
        self.fields['deadline'].help_text = "Required completion date (if applicable)"
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        
        # Set created_by if this is a new job
        if not instance.pk and self.user:
            instance.created_by = self.user
        
        if commit:
            instance.save()
            
        return instance


class JobMilestoneForm(forms.ModelForm):
    """Form for adding or editing job milestones"""
    
    class Meta:
        model = JobMilestone
        fields = ['name', 'description', 'due_date', 'completed', 'order']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
            'due_date': forms.DateInput(attrs={'type': 'date'}),
        }
    
    def __init__(self, *args, **kwargs):
        self.job = kwargs.pop('job', None)
        super().__init__(*args, **kwargs)
        
        # Add help text
        self.fields['name'].help_text = "Milestone name (e.g., Design Approval, Prototype)"
        self.fields['order'].help_text = "Order for display (lower numbers first)"
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        
        if self.job:
            instance.job = self.job
        
        # If marking as completed, set completed date
        if instance.completed and not instance.completed_date:
            instance.completed_date = timezone.now().date()
        
        if commit:
            instance.save()
            
        return instance


class JobStatusForm(forms.ModelForm):
    """Form for creating and editing job statuses"""
    
    class Meta:
        model = JobStatus
        fields = ['name', 'description', 'color_code', 'order']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 2}),
            'color_code': forms.TextInput(attrs={'type': 'color'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Add help text
        self.fields['name'].help_text = "Status name (e.g., In Progress, Completed)"
        self.fields['color_code'].help_text = "Color for visual indicators"
        self.fields['order'].help_text = "Display order in status lists"
