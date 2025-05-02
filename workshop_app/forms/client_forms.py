from django import forms
from ..models import Client, ContactPerson, ClientDocument

class ClientForm(forms.ModelForm):
    """Form for creating and updating clients"""
    
    class Meta:
        model = Client
        fields = [
            'name', 'type', 'industry', 'reference_source',
            'status', 'notes',
            'primary_email', 'secondary_email', 'phone_number', 'mobile_number',
            'website', 'social_media',
            'street_address', 'address_line_2', 'city', 'state_province',
            'postal_code', 'country',
            'tax_id', 'payment_terms', 'currency', 'discount_rate',
            'credit_limit', 'account_status'
        ]
        widgets = {
            'notes': forms.Textarea(attrs={'rows': 3}),
            'social_media': forms.Textarea(attrs={'rows': 2}),
            'client_id': forms.TextInput(attrs={'readonly': 'readonly'}),
            'discount_rate': forms.NumberInput(attrs={'step': '0.01', 'min': '0', 'max': '100'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Add fieldsets
        self.fieldsets = [
            ('Basic Information', ['name', 'type', 'industry', 'reference_source', 'status']),
            ('Contact Information', ['primary_email', 'secondary_email', 'phone_number', 'mobile_number', 
                                    'website', 'social_media']),
            ('Address', ['street_address', 'address_line_2', 'city', 'state_province', 
                         'postal_code', 'country']),
            ('Financial Information', ['tax_id', 'payment_terms', 'currency', 'discount_rate', 
                                      'credit_limit', 'account_status']),
            ('Additional Information', ['notes']),
        ]
        
        # Add help text
        self.fields['name'].help_text = "Company or individual name"
        self.fields['primary_email'].help_text = "Main email address for communication"
        self.fields['social_media'].help_text = "One URL per line (LinkedIn, Twitter, etc.)"
        self.fields['tax_id'].help_text = "Tax ID or VAT number"

class ContactPersonForm(forms.ModelForm):
    """Form for adding and editing contact people"""
    
    class Meta:
        model = ContactPerson
        fields = [
            'name', 'position', 'department', 'primary_contact',
            'direct_email', 'phone', 'mobile',
            'communication_preference', 'working_hours',
            'notes'
        ]
        widgets = {
            'notes': forms.Textarea(attrs={'rows': 3}),
            'working_hours': forms.TextInput(attrs={'placeholder': 'e.g., Mon-Fri 9am-5pm'}),
        }
    
    def __init__(self, *args, **kwargs):
        self.client = kwargs.pop('client', None)
        super().__init__(*args, **kwargs)
        
        # Add help text
        self.fields['primary_contact'].help_text = "Designate this person as the main contact"
        self.fields['communication_preference'].help_text = "Preferred method of contact"
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        
        if self.client:
            instance.client = self.client
            
        if commit:
            instance.save()
            
        return instance

class ClientDocumentForm(forms.ModelForm):
    """Form for uploading client documents"""
    
    class Meta:
        model = ClientDocument
        fields = [
            'doc_type', 'title', 'expiration_date',
            'file', 'tags', 'notes'
        ]
        widgets = {
            'expiration_date': forms.DateInput(attrs={'type': 'date'}),
            'notes': forms.Textarea(attrs={'rows': 3}),
        }
    
    def __init__(self, *args, **kwargs):
        self.client = kwargs.pop('client', None)
        super().__init__(*args, **kwargs)
        
        # Add help text
        self.fields['doc_type'].help_text = "Type of document being uploaded"
        self.fields['tags'].help_text = "Comma-separated list of tags (e.g., contract, 2023, signed)"
        self.fields['expiration_date'].help_text = "Date when document expires (if applicable)"
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        
        if self.client:
            instance.client = self.client
            
        if commit:
            instance.save()
            
        return instance
