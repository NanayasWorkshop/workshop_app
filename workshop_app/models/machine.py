from django.db import models
from django.core.files.base import ContentFile
import qrcode
import io

class MachineType(models.Model):
    """Types of machines: FDM, CNC, LCUT, etc."""
    code = models.CharField(max_length=10, unique=True)  # FDM, DLP, CNC, etc.
    name = models.CharField(max_length=50)  # Full name
    description = models.TextField(blank=True)
    
    def __str__(self):
        return f"{self.code} - {self.name}"


class Machine(models.Model):
    """Individual machine entries"""
    # Basic Info
    machine_id = models.CharField(max_length=15, unique=True)  # FDM-001
    name = models.CharField(max_length=100)  # Prusa MK3S+
    machine_type = models.ForeignKey(MachineType, on_delete=models.CASCADE, related_name='machines')
    manufacturer = models.CharField(max_length=100, blank=True)
    model_number = models.CharField(max_length=100, blank=True)
    serial_number = models.CharField(max_length=100, blank=True)
    location_in_workshop = models.CharField(max_length=100, blank=True)
    
    # Purchase Info
    purchase_date = models.DateField(null=True, blank=True)
    purchase_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    supplier = models.CharField(max_length=100, blank=True)
    warranty_end_date = models.DateField(null=True, blank=True)
    
    # Technical Specs
    working_area = models.CharField(max_length=100, blank=True)  # LxWxH in mm
    power_requirements = models.CharField(max_length=100, blank=True)
    maximum_work_speed = models.CharField(max_length=50, blank=True)
    precision = models.CharField(max_length=50, blank=True)
    
    # Operational Costs
    hourly_rate = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    setup_time = models.IntegerField(null=True, blank=True)  # minutes
    setup_rate = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    cleanup_time = models.IntegerField(null=True, blank=True)  # minutes
    cleanup_rate = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    
    # Status
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('maintenance', 'In Maintenance'),
        ('out_of_order', 'Out of Order')
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    # Temporarily commented out to avoid circular dependency
    # current_job = models.ForeignKey('Job', null=True, blank=True, on_delete=models.SET_NULL)
    reserved_until = models.DateTimeField(null=True, blank=True)
    
    # QR Code
    qr_code = models.ImageField(upload_to='qr_codes/machines/', blank=True)
    
    def __str__(self):
        return f"{self.machine_id} - {self.name}"
    
    def save(self, *args, **kwargs):
        # Generate QR code if it doesn't exist and machine_id is set
        if not self.qr_code and self.machine_id:
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=10,
                border=4,
            )
            qr.add_data(self.machine_id)
            qr.make(fit=True)

            img = qr.make_image(fill_color="black", back_color="white")
            buffer = io.BytesIO()
            img.save(buffer)
            filename = f'qr_machine_{self.machine_id}.png'
            self.qr_code.save(filename, ContentFile(buffer.getvalue()), save=False)
        
        # Call the parent save method
        super().save(*args, **kwargs)
    
    def is_available(self):
        """Check if the machine is currently available"""
        return self.status == 'active' and self.reserved_until is None


class Job(models.Model):
    """Placeholder Job model to support Machine model foreign key"""
    job_id = models.CharField(max_length=15, unique=True)
    project_name = models.CharField(max_length=100)
    
    def __str__(self):
        return f"{self.job_id} - {self.project_name}"
