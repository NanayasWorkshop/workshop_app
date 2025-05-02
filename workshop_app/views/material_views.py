from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from django.db.models import Q
from django.http import HttpResponseRedirect
from django.urls import reverse

from ..models import Material, MaterialCategory, MaterialType, MaterialEntry, MaterialAttachment, AttachmentType
from ..forms import MaterialForm, MaterialEntryForm, MaterialAttachmentForm


@login_required
def material_list(request):
    """
    Display a list of all materials in the inventory.
    """
    # Get filter parameters from request
    category_code = request.GET.get('category', '')
    type_code = request.GET.get('type', '')
    search_query = request.GET.get('search', '')
    
    # Start with all materials
    materials = Material.objects.all()
    
    # Apply filters if provided
    if category_code:
        materials = materials.filter(material_type__category__code=category_code)
    
    if type_code:
        materials = materials.filter(material_type__code=type_code)
    
    if search_query:
        materials = materials.filter(
            Q(name__icontains=search_query) | 
            Q(material_id__icontains=search_query) |
            Q(supplier_name__icontains=search_query) |
            Q(serial_number__icontains=search_query) |
            Q(supplier_sku__icontains=search_query)
        )
    
    # Get all categories for the filter dropdown
    categories = MaterialCategory.objects.all()
    
    # Get material types based on selected category
    material_types = []
    if category_code:
        material_types = MaterialType.objects.filter(category__code=category_code)
    
    # Count low stock items
    low_stock_count = sum(1 for m in materials if m.is_low_stock())
    
    context = {
        'materials': materials,
        'categories': categories,
        'material_types': material_types,
        'selected_category': category_code,
        'selected_type': type_code,
        'search_query': search_query,
        'low_stock_count': low_stock_count,
    }
    
    return render(request, 'workshop_app/materials/list.html', context)


@login_required
def material_detail(request, material_id):
    """
    Display detailed information about a specific material.
    """
    # Try to find by material_id or serial_number
    material = get_object_or_404(
        Material, 
        Q(material_id=material_id) | Q(serial_number=material_id)
    )
    
    # Get material entries for history
    entries = material.entries.all().order_by('-purchase_date')
    
    # Get material attachments grouped by type
    attachment_types = AttachmentType.objects.filter(
        attachments__material=material
    ).distinct()
    
    # Create a dictionary of attachments by type
    grouped_attachments = {}
    for attachment_type in attachment_types:
        grouped_attachments[attachment_type] = material.attachments.filter(
            attachment_type=attachment_type
        ).order_by('upload_date')
    
    # Handle attachment upload
    if request.method == 'POST' and 'upload_attachment' in request.POST:
        attachment_form = MaterialAttachmentForm(
            request.POST, 
            request.FILES,
            material=material,
            user=request.user
        )
        if attachment_form.is_valid():
            # Save the main file
            attachment = attachment_form.save()
            
            # Process multiple file uploads (if any)
            multiple_files = request.FILES.getlist('files[]')
            count = 1
            
            for f in multiple_files:
                # For each additional file, create a new attachment with same metadata
                new_attachment = MaterialAttachment(
                    material=material,
                    attachment_type=attachment.attachment_type,
                    description=f"{attachment.description} ({count})" if attachment.description else f"File {count}",
                    file=f,
                    uploaded_by=request.user
                )
                new_attachment.save()
                count += 1
                
            if multiple_files:
                messages.success(request, f'Successfully uploaded {1 + len(multiple_files)} attachments.')
            else:
                messages.success(request, 'Attachment uploaded successfully.')
                
            return HttpResponseRedirect(request.path)
    else:
        attachment_form = MaterialAttachmentForm(material=material, user=request.user)
    
    # Get available attachment types for dropdown
    attachment_types_list = AttachmentType.objects.all().order_by('name')
    
    context = {
        'material': material,
        'entries': entries,
        'grouped_attachments': grouped_attachments,
        'attachment_types': attachment_types_list,
        'attachment_form': attachment_form,
    }
    
    return render(request, 'workshop_app/materials/detail.html', context)


@login_required
def material_create(request):
    """
    Create a new material and its first entry.
    """
    # Check for scanned_id parameter to pre-fill serial number
    scanned_id = request.GET.get('scanned_id', '')
    
    if request.method == 'POST':
        form = MaterialForm(request.POST)
        entry_form = MaterialEntryForm(request.POST, request.FILES)
        
        if form.is_valid() and entry_form.is_valid():
            with transaction.atomic():
                # Save material with zero stock first
                material = form.save(commit=False)
                material.current_stock = 0
                material.price_per_unit = entry_form.cleaned_data['price_per_unit']
                material.purchase_date = entry_form.cleaned_data['purchase_date']
                material.created_by = request.user  # Set the creator
                material.save()
                
                # Create entry linked to the material
                entry = entry_form.save(commit=False)
                entry.material = material
                entry.save()
                
                # Update material stock and price
                material.update_price_and_stock()
            
            messages.success(request, 'Material created successfully.')
            return redirect('workshop_app:material_detail', material_id=material.material_id)
    else:
        # Pre-fill serial number if scanned_id is provided
        initial = {}
        if scanned_id:
            initial = {'serial_number': scanned_id}
            messages.info(request, f'Serial number pre-filled from scan: {scanned_id}')
            
        form = MaterialForm(initial=initial)
        entry_form = MaterialEntryForm()
    
    context = {
        'form': form,
        'entry_form': entry_form,
        'is_new': True,
        'title': 'Add New Material',
    }
    
    return render(request, 'workshop_app/materials/form.html', context)


@login_required
def material_update(request, material_id):
    """
    Update an existing material's information.
    """
    material = get_object_or_404(Material, material_id=material_id)
    
    if request.method == 'POST':
        form = MaterialForm(request.POST, instance=material)
        if form.is_valid():
            form.save()
            messages.success(request, 'Material updated successfully.')
            return redirect('workshop_app:material_detail', material_id=material.material_id)
    else:
        form = MaterialForm(instance=material)
    
    context = {
        'form': form,
        'material': material,
        'is_new': False,
        'title': 'Edit Material',
    }
    
    return render(request, 'workshop_app/materials/form.html', context)


@login_required
def material_entry_add(request, material_id):
    """
    Add a new entry (purchase) to an existing material.
    """
    material = get_object_or_404(Material, material_id=material_id)
    
    if request.method == 'POST':
        form = MaterialEntryForm(request.POST, request.FILES, material=material)
        if form.is_valid():
            entry = form.save(commit=False)
            entry.material = material
            entry.save()
            
            # Update material average price and stock
            material.update_price_and_stock()
            
            messages.success(request, 'Material entry added successfully.')
            return redirect('workshop_app:material_detail', material_id=material.material_id)
    else:
        form = MaterialEntryForm(material=material)
    
    context = {
        'form': form,
        'material': material,
        'title': 'Add Material Purchase Entry',
    }
    
    return render(request, 'workshop_app/materials/entry_form.html', context)


@login_required
def material_delete(request, material_id):
    """
    Delete a material and all its entries.
    """
    material = get_object_or_404(Material, material_id=material_id)
    
    if request.method == 'POST':
        material.delete()
        messages.success(request, 'Material deleted successfully.')
        return redirect('workshop_app:material_list')
    
    context = {
        'material': material,
    }
    
    return render(request, 'workshop_app/materials/confirm_delete.html', context)


@login_required
def material_attachment_delete(request, attachment_id):
    """
    Delete a material attachment.
    """
    attachment = get_object_or_404(MaterialAttachment, id=attachment_id)
    material = attachment.material
    
    if request.method == 'POST':
        attachment.delete()
        messages.success(request, 'Attachment deleted successfully.')
        return redirect('workshop_app:material_detail', material_id=material.material_id)
    
    context = {
        'attachment': attachment,
        'material': material,
    }
    
    return render(request, 'workshop_app/materials/attachment_confirm_delete.html', context)
