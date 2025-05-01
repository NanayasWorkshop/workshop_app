from django.db import models
from .material import Material
from django.contrib.auth.models import User


class AttachmentType(models.Model):
    """Types of material attachments"""
    name = models.CharField(max_length=50, unique=True)  # Datasheet, Image, etc.
    
    def __str__(self):
        return self.name


class MaterialAttachment(models.Model):
    """File attachments for materials"""
    material = models.ForeignKey(Material, on_delete=models.CASCADE, related_name='attachments')
    attachment_type = models.ForeignKey(AttachmentType, on_delete=models.PROTECT, related_name='attachments')
    custom_type = models.CharField(max_length=50, blank=True, help_text="Custom type if not in dropdown")
    description = models.CharField(max_length=100, blank=True)
    file = models.FileField(upload_to='material_attachments/')
    uploaded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='uploaded_attachments')
    upload_date = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        type_name = self.custom_type if self.custom_type else self.attachment_type.name
        return f"{type_name} for {self.material.material_id}"
    
    def get_type_display(self):
        """Get the display name for the attachment type"""
        if self.custom_type:
            return self.custom_type
        return self.attachment_type.name
    
    def get_file_extension(self):
        """Get the file extension"""
        return self.file.name.split('.')[-1].lower() if '.' in self.file.name else ''
    
    def is_image(self):
        """Check if the file is an image"""
        image_extensions = ['jpg', 'jpeg', 'png', 'gif', 'bmp', 'webp']
        return self.get_file_extension() in image_extensions
    
    def is_pdf(self):
        """Check if the file is a PDF"""
        return self.get_file_extension() == 'pdf'
    
    class Meta:
        ordering = ['attachment_type', 'upload_date']
