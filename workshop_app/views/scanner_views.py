from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q

from ..models import Material, MaterialAttachment, AttachmentType, StaffSettings

@login_required
def scanner_view(request):
    """Main scanner interface page"""
    context = {
        'title': 'Material Scanner',
    }
    return render(request, 'workshop_app/materials/scanner.html', context)

@login_required
def material_lookup(request):
    """
    API endpoint to look up a material by ID or serial number
    Returns JSON with material details or error
    """
    identifier = request.GET.get('identifier', '')
    
    if not identifier:
        return JsonResponse({'error': 'No identifier provided'}, status=400)
    
    try:
        # Check if the identifier contains a pipe character (from QR code)
        if '|' in identifier:
            # Split the identifier by pipe
            parts = identifier.split('|')
            # Try to find by either part
            material = Material.objects.get(
                Q(material_id=parts[0]) | Q(serial_number=parts[0]) |
                Q(material_id=parts[1]) | Q(serial_number=parts[1])
            )
        else:
            # Original search logic for identifiers without pipe
            material = Material.objects.get(
                Q(material_id=identifier) | Q(serial_number=identifier)
            )
            
        # Look for a product image
        product_image = None
        try:
            product_attachment_type = AttachmentType.objects.get(name='Product')
            product_image = MaterialAttachment.objects.filter(
                material=material,
                attachment_type=product_attachment_type
            ).first()
        except AttachmentType.DoesNotExist:
            # Product attachment type doesn't exist
            pass
        
        # Get active job from user settings
        active_job = None
        try:
            staff_settings = StaffSettings.objects.get(user=request.user)
            active_job = staff_settings.active_job
        except StaffSettings.DoesNotExist:
            pass
            
        # Return material details as JSON
        data = {
            'found': True,
            'material_id': material.material_id,
            'serial_number': material.serial_number,
            'name': material.name,
            'type': material.material_type.name,
            'current_stock': float(material.current_stock),
            'unit': material.unit_of_measurement,
            'supplier_name': material.supplier_name,
            'price_per_unit': str(material.price_per_unit) if material.price_per_unit else '',
            'detail_url': f"/materials/{material.material_id}/",
            'has_product_image': product_image is not None,
            'has_active_job': active_job is not None,
        }
        
        # Add job-related URLs if there's an active job
        if active_job:
            data['job_material_url'] = f"/jobs/material/add/?material_id={material.material_id}"
            data['active_job_name'] = active_job.project_name
            data['active_job_id'] = active_job.job_id
        
        # Add the image URL if available
        if product_image:
            data['product_image_url'] = product_image.file.url
        
        return JsonResponse(data)
        
    except Material.DoesNotExist:
        return JsonResponse({
            'found': False,
            'error': 'Material not found',
            'message': f'No material found with ID or serial number: {identifier}',
            'scanned_id': identifier  # Include the scanned ID in the response
        }, status=404)
    
    except Exception as e:
        return JsonResponse({
            'found': False,
            'error': 'Error looking up material',
            'message': str(e),
            'scanned_id': identifier  # Include the scanned ID in the response
        }, status=500)
