from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

class Client(models.Model):
    """Model representing a client (company or individual)"""
    
    # Types of clients
    CLIENT_TYPES = [
        ('company', 'Company'),
        ('individual', 'Individual'),
    ]
    
    # Client statuses
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('prospect', 'Prospect'),
        ('former', 'Former'),
    ]
    
    # Basic Information
    client_id = models.CharField(max_length=20, unique=True, help_text="Unique client identifier")
    name = models.CharField(max_length=100, help_text="Company or individual name")
    type = models.CharField(max_length=10, choices=CLIENT_TYPES, default='company')
    industry = models.CharField(max_length=100, blank=True, help_text="Category of client's business")
    reference_source = models.CharField(max_length=100, blank=True, help_text="How the client found us")
    notes = models.TextField(blank=True, help_text="General notes about the client")
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='active')
    created_date = models.DateTimeField(default=timezone.now)
    last_updated = models.DateTimeField(auto_now=True)
    
    # Contact Information
    primary_email = models.EmailField(blank=True)
    secondary_email = models.EmailField(blank=True)
    phone_number = models.CharField(max_length=20, blank=True)
    mobile_number = models.CharField(max_length=20, blank=True)
    website = models.URLField(blank=True)
    social_media = models.TextField(blank=True, help_text="Links to client's social profiles")
    
    # Address
    street_address = models.CharField(max_length=100, blank=True)
    address_line_2 = models.CharField(max_length=100, blank=True)
    city = models.CharField(max_length=100, blank=True)
    state_province = models.CharField(max_length=100, blank=True)
    postal_code = models.CharField(max_length=20, blank=True)
    country = models.CharField(max_length=100, blank=True)
    
    # Financial Information
    tax_id = models.CharField(max_length=50, blank=True, help_text="Tax ID / VAT Number")
    payment_terms = models.CharField(max_length=50, blank=True, help_text="Net 30, COD, etc.")
    currency = models.CharField(max_length=10, blank=True, default="CHF")
    discount_rate = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    credit_limit = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    account_status = models.CharField(max_length=50, blank=True, help_text="Good Standing, Credit Hold, etc.")
    
    def __str__(self):
        return f"{self.client_id} - {self.name}"
    
    def save(self, *args, **kwargs):
        # Auto-generate client_id if not provided
        if not self.client_id:
            # Get current year
            year = timezone.now().year
            
            # Find the highest client number for current year
            last_client = Client.objects.filter(
                client_id__startswith=f"CLI-{year}"
            ).order_by('-client_id').first()
            
            if last_client:
                # Extract the sequential number and increment
                try:
                    last_num = int(last_client.client_id.split('-')[-1])
                    next_num = last_num + 1
                except (ValueError, IndexError):
                    next_num = 1
            else:
                next_num = 1
                
            # Format: CLI-YYYY-XXXX
            self.client_id = f"CLI-{year}-{next_num:04d}"
            
        super().save(*args, **kwargs)

class ContactPerson(models.Model):
    """Person associated with a client"""
    
    # Basic Information
    name = models.CharField(max_length=100)
    position = models.CharField(max_length=100, blank=True)
    department = models.CharField(max_length=100, blank=True)
    primary_contact = models.BooleanField(default=False)
    notes = models.TextField(blank=True)
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name='contacts')
    
    # Contact Details
    direct_email = models.EmailField(blank=True)
    phone = models.CharField(max_length=20, blank=True)
    mobile = models.CharField(max_length=20, blank=True)
    communication_preference = models.CharField(max_length=20, blank=True, 
                                               help_text="Email/Phone/In-person preference")
    working_hours = models.CharField(max_length=100, blank=True)
    
    def __str__(self):
        return f"{self.name} - {self.client.name}"

class ClientHistory(models.Model):
    """Tracks client project history and communication"""
    
    # Project History
    client = models.OneToOneField(Client, on_delete=models.CASCADE, related_name='history')
    projects_completed = models.IntegerField(default=0)
    total_spending = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    average_project_value = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    first_project_date = models.DateField(null=True, blank=True)
    latest_project_date = models.DateField(null=True, blank=True)
    
    def __str__(self):
        return f"History for {self.client.name}"
    
    def update_stats(self):
        """Update history statistics based on completed projects"""
        if self.projects_completed > 0 and self.total_spending > 0:
            self.average_project_value = self.total_spending / self.projects_completed
        else:
            self.average_project_value = None

class Communication(models.Model):
    """Individual communication log entry with a client"""
    
    # Communication types
    COMM_TYPES = [
        ('email', 'Email'),
        ('phone', 'Phone'),
        ('meeting', 'Meeting'),
        ('other', 'Other'),
    ]
    
    # Communication details
    client_history = models.ForeignKey(ClientHistory, on_delete=models.CASCADE, related_name='communications')
    date = models.DateTimeField(default=timezone.now)
    comm_type = models.CharField(max_length=10, choices=COMM_TYPES, default='email')
    contact_person = models.ForeignKey(ContactPerson, on_delete=models.SET_NULL, null=True, blank=True)
    staff_member = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    summary = models.TextField(help_text="Brief description of communication")
    attachment = models.FileField(upload_to='client_communications/', blank=True, null=True)
    follow_up_required = models.BooleanField(default=False)
    follow_up_date = models.DateField(null=True, blank=True)
    
    def __str__(self):
        return f"{self.get_comm_type_display()} with {self.client_history.client.name} on {self.date.strftime('%Y-%m-%d')}"

class ClientDocument(models.Model):
    """Documents associated with a client"""
    
    # Document types
    DOC_TYPES = [
        ('quote', 'Quote'),
        ('invoice', 'Invoice'),
        ('contract', 'Contract'),
        ('other', 'Other'),
    ]
    
    # Document details
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name='documents')
    doc_type = models.CharField(max_length=10, choices=DOC_TYPES)
    title = models.CharField(max_length=100)
    upload_date = models.DateTimeField(default=timezone.now)
    expiration_date = models.DateField(null=True, blank=True)
    file = models.FileField(upload_to='client_documents/')
    tags = models.CharField(max_length=200, blank=True, help_text="Comma-separated tags")
    notes = models.TextField(blank=True)
    
    def __str__(self):
        return f"{self.get_doc_type_display()}: {self.title} - {self.client.name}"
