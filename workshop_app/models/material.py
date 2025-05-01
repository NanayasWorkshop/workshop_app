from django.db import models
from django.core.files.base import ContentFile
from django.contrib.auth.models import User
from django.utils import timezone
import qrcode
import io
from PIL import Image


class MaterialCategory(models.Model):
    """Categories like PRT (3D Printer), CNC, LSR (Laser), etc."""
    code = models.CharField(max_length=5, unique=True)  # PRT, CNC, LSR, etc.
    name = models.CharField(max_length=50)  # Full name of category
    description = models.TextField(blank=True)
    
    class Meta:
        verbose_name_plural = "Material Categories"
    
    def __str__(self):
        return f"{self.code} - {self.name}"


class MaterialType(models.Model):
    """Types like PLA, Wood, Acrylic, etc."""
    category = models.ForeignKey(MaterialCategory, on_delete=models.CASCADE, related_name='material_types')
    code = models.CharField(max_length=10)  # PLA, WOOD, ACR, etc.
    name = models.CharField(max_length=50)  # Full name of material type
    description = models.TextField(blank=True)
    
    class Meta:
        unique_together = ['category', 'code']
    
    def __str__(self):
        return f"{self.category.code}-{self.code} - {self.name}"

    def get_display_code(self):
        """Get the combined code for this material type"""
        return f"{self.category.code}-{self.code}"


class Material(models.Model):
    """Individual material entries"""
    # Basic Info
    material_id = models.CharField(max_length=15, unique=True)  # PRT-PLA-0001
    serial_number = models.CharField(max_length=50, blank=True, help_text="Manufacturer's serial number if applicable")
    supplier_sku = models.CharField(max_length=50, blank=True, help_text="Supplier's SKU or product code")
    name = models.CharField(max_length=100)
    material_type = models.ForeignKey(MaterialType, on_delete=models.CASCADE, related_name='materials')
    color = models.CharField(max_length=50, blank=True)
    dimensions = models.CharField(max_length=100, blank=True)  # For sheet materials
    unit_of_measurement = models.CharField(max_length=20)  # kg, sheet, m, etc.
    
    # Supplier Info
    supplier_name = models.CharField(max_length=100, blank=True)
    brand_name = models.CharField(max_length=100, blank=True)
    
    # Inventory Management
    current_stock = models.DecimalField(max_digits=10, decimal_places=2)
    minimum_stock_level = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    minimum_stock_alert = models.BooleanField(default=False)
    location_in_workshop = models.CharField(max_length=100, blank=True)
    
    # Purchase Details
    purchase_date = models.DateField(null=True, blank=True)
    price_per_unit = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    expiration_date = models.DateField(null=True, blank=True)
    
    # User Tracking - using default value to handle existing rows
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='created_materials')
    created_at = models.DateTimeField(default=timezone.now)  # Using default instead of auto_now_add
    updated_at = models.DateTimeField(auto_now=True)
    
    # Optional
    project_association = models.CharField(max_length=100, blank=True)
    notes = models.TextField(blank=True)
    qr_code = models.ImageField(upload_to='qr_codes/materials/', blank=True)
    
    def __str__(self):
        display = f"{self.material_id} - {self.name}"
        if self.color:
            display += f" - {self.color}"
        return display
    
    def get_display_name(self):
        """Get a display name with type code and color"""
        display = f"{self.material_type.get_display_code()} - {self.name}"
        if self.color:
            display += f" - {self.color}"
        return display
    
    def save(self, *args, **kwargs):
        # Auto-generate material_id if it's a new record
        if not self.pk and not self.material_id:
            self.generate_material_id()
            
        # Set created_at for new objects only
        if not self.pk:
            self.created_at = timezone.now()
            
        # Generate QR code if it doesn't exist and material_id is set
        if not self.qr_code and self.material_id:
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=10,
                border=4,
            )
            # Include both material_id and serial_number in QR code if available
            qr_data = self.material_id
            if self.serial_number:
                qr_data += f"|{self.serial_number}"
            
            qr.add_data(qr_data)
            qr.make(fit=True)

            img = qr.make_image(fill_color="black", back_color="white")
            buffer = io.BytesIO()
            img.save(buffer)
            filename = f'qr_material_{self.material_id}.png'
            self.qr_code.save(filename, ContentFile(buffer.getvalue()), save=False)
        
        # Call the parent save method
        super().save(*args, **kwargs)
    
    def generate_material_id(self):
        """Auto-generate material ID using category, type and serial number"""
        # Get the category and type codes
        category_code = self.material_type.category.code
        type_code = self.material_type.code
        
        # Base part of the ID
        base_id = f"{category_code}-{type_code}-"
        
        # Try to use last 4 digits of serial number if available
        if self.serial_number and len(self.serial_number) >= 4:
            # Get last 4 digits, or pad with zeros if shorter
            last_digits = self.serial_number[-4:].zfill(4)
            self.material_id = f"{base_id}{last_digits}"
        else:
            # If no serial number, find the next available number
            # Get the highest number for this category and type
            existing_materials = Material.objects.filter(
                material_id__startswith=base_id
            ).order_by('-material_id')
            
            if existing_materials.exists():
                # Extract the number part and increment
                last_id = existing_materials.first().material_id
                try:
                    last_number = int(last_id.split('-')[-1])
                    next_number = last_number + 1
                except (ValueError, IndexError):
                    next_number = 1
            else:
                next_number = 1
                
            # Format with leading zeros
            self.material_id = f"{base_id}{next_number:04d}"
    
    def is_low_stock(self):
        """Check if the material is running low on stock"""
        if self.minimum_stock_level and self.current_stock <= self.minimum_stock_level:
            return True
        return False
    
    def update_price_and_stock(self):
        """Update average price and stock based on entries"""
        from .material_entry import MaterialEntry
        entries = MaterialEntry.objects.filter(material=self)
        
        if entries.exists():
            # Calculate total quantity and weighted price
            total_quantity = sum(entry.quantity for entry in entries)
            total_value = sum(entry.quantity * entry.price_per_unit for entry in entries)
            
            # Update stock and average price
            self.current_stock = total_quantity
            if total_quantity > 0:
                self.price_per_unit = total_value / total_quantity
            
            # Save without triggering another update
            Material.objects.filter(id=self.id).update(
                current_stock=self.current_stock,
                price_per_unit=self.price_per_unit
            )
    
    def record_consumption(self, quantity, job_reference='', operator_name='', notes=''):
        """Record material consumption and update stock"""
        from .transaction import MaterialTransaction
        
        if quantity > self.current_stock:
            raise ValueError(f"Cannot consume {quantity} {self.unit_of_measurement}. Only {self.current_stock} available.")
        
        transaction = MaterialTransaction(
            material=self,
            quantity=quantity,
            transaction_type='consumption',
            job_reference=job_reference,
            operator_name=operator_name,
            notes=notes
        )
        transaction.save()
        
        return transaction

    def record_return(self, quantity, job_reference='', operator_name='', notes=''):
        """Record material return and update stock"""
        from .transaction import MaterialTransaction
        
        transaction = MaterialTransaction(
            material=self,
            quantity=quantity,
            transaction_type='return',
            job_reference=job_reference,
            operator_name=operator_name,
            notes=notes
        )
        transaction.save()
        
        return transaction
