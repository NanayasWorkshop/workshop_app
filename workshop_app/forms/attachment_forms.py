from django import forms
from ..models import MaterialAttachment, AttachmentType


class MaterialAttachmentForm(forms.ModelForm):
    """Form for adding file attachments to materials"""
    new_type = forms.CharField(
        max_length=50, 
        required=False, 
        help_text="Enter a new attachment type if not in the dropdown"
    )
    
    class Meta:
        model = MaterialAttachment
        fields = ['attachment_type', 'new_type', 'description', 'file']
        
    def __init__(self, *args, **kwargs):
        self.material = kwargs.pop('material', None)
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Set help text
        self.fields['attachment_type'].help_text = "Select the type of attachment"
        self.fields['description'].help_text = "Brief description of this file"
        self.fields['file'].help_text = "Upload file (use batch upload for multiple files)"
        
        # Set attachment type choices
        attachment_types = AttachmentType.objects.all().order_by('name')
        if attachment_types.exists():
            self.fields['attachment_type'].choices = [(at.id, at.name) for at in attachment_types]
            self.fields['attachment_type'].choices.insert(0, ('', '-- Select Type --'))
        
    def clean(self):
        """Validate the form data"""
        cleaned_data = super().clean()
        attachment_type = cleaned_data.get('attachment_type')
        new_type = cleaned_data.get('new_type')
        
        # If new type is provided, create a new AttachmentType
        if new_type and not attachment_type:
            # Check if type already exists (case insensitive)
            existing_type = AttachmentType.objects.filter(name__iexact=new_type).first()
            if existing_type:
                cleaned_data['attachment_type'] = existing_type
                cleaned_data['custom_type'] = ''
            else:
                # Create new type
                new_attachment_type = AttachmentType(name=new_type)
                if not self.instance.pk:  # Only create when not updating
                    new_attachment_type.save()
                cleaned_data['attachment_type'] = new_attachment_type
                cleaned_data['custom_type'] = ''
        
        return cleaned_data
    
    def save(self, commit=True):
        """Override save to add the material and user reference"""
        instance = super().save(commit=False)
        
        if self.material:
            instance.material = self.material
            
        if self.user:
            instance.uploaded_by = self.user
            
        # Set custom_type if a new type is provided
        new_type = self.cleaned_data.get('new_type')
        if new_type and not self.cleaned_data.get('attachment_type'):
            instance.custom_type = new_type
            
        if commit:
            instance.save()
            
        return instance
