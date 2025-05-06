from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from django.http import HttpResponseRedirect, Http404
from django.utils import timezone

from ..models import Job, JobMaterial, Material, StaffSettings
from ..forms import JobMaterialForm, JobMaterialScanForm

@login_required
def job_material_add(request, job_id=None):
    """
    Add material usage to a job.
    If job_id is not provided, use the active job.
    """
    # Determine which job to use
    if job_id:
        job = get_object_or_404(Job, job_id=job_id)
    else:
        # Get active job from user settings
        try:
            staff_settings = StaffSettings.objects.get(user=request.user)
            job = staff_settings.active_job
            if not job:
                # Redirect to scanner to select a job
                messages.warning(request, "Please activate a job first.")
                return redirect('workshop_app:job_scanner_view')
        except StaffSettings.DoesNotExist:
            messages.warning(request, "Please activate a job first.")
            return redirect('workshop_app:job_scanner_view')
    
    # Check for material_id in GET for scan workflow
    material_id = request.GET.get('material_id', '')
    if material_id:
        # Try to look up the material
        try:
            material = Material.objects.get(
                Q(material_id=material_id) | Q(serial_number=material_id)
            )
            
            # Handle form submission for scanned material
            if request.method == 'POST':
                form = JobMaterialScanForm(request.POST, material=material)
                if form.is_valid():
                    # Create JobMaterial record
                    job_material = JobMaterial(
                        job=job,
                        material=material,
                        quantity=form.cleaned_data['quantity'],
                        result=form.cleaned_data['result'],
                        notes=form.cleaned_data['notes'],
                        added_by=request.user.get_full_name() or request.user.username,
                        date_used=timezone.now()
                    )
                    
                    # Set unit price from material if available
                    if material.price_per_unit:
                        job_material.unit_price = material.price_per_unit
                    
                    job_material.save()
                    
                    # Update material stock (if not a return)
                    if form.cleaned_data['result'] != 'returned':
                        material.current_stock -= form.cleaned_data['quantity']
                        material.save(update_fields=['current_stock'])
                    
                    # Update job financial summary
                    job.create_financial_summary()
                    
                    messages.success(
                        request, 
                        f"Added {form.cleaned_data['quantity']} {material.unit_of_measurement} "
                        f"of {material.name} to job '{job.project_name}'"
                    )
                    
                    # Redirect to scanner to scan more
                    return redirect('workshop_app:job_scanner_view')
            else:
                form = JobMaterialScanForm(material=material)
                
            # Show scan form for this material
            context = {
                'form': form,
                'material': material,
                'job': job,
                'title': f"Add {material.name} to {job.project_name}",
                'scan_workflow': True,
            }
            
            return render(request, 'workshop_app/jobs/material_scan_form.html', context)
            
        except Material.DoesNotExist:
            messages.error(request, f"Material with ID '{material_id}' not found.")
            return redirect('workshop_app:job_scanner_view')
    
    # Standard (non-scan) form
    if request.method == 'POST':
        form = JobMaterialForm(request.POST, job=job, user=request.user)
        if form.is_valid():
            job_material = form.save()
            messages.success(
                request, 
                f"Added {job_material.quantity} {job_material.material.unit_of_measurement} "
                f"of {job_material.material.name} to job"
            )
            
            # Redirect back to job detail
            return redirect('workshop_app:job_detail', job_id=job.job_id)
    else:
        form = JobMaterialForm(job=job, user=request.user)
    
    context = {
        'form': form,
        'job': job,
        'title': f"Add Material Usage to {job.project_name}",
        'scan_workflow': False,
    }
    
    return render(request, 'workshop_app/jobs/material_form.html', context)

@login_required
def job_material_delete(request, material_id):
    """
    Delete a material usage record from a job.
    """
    job_material = get_object_or_404(JobMaterial, id=material_id)
    job = job_material.job
    
    # Check if user has permission (simple for now - any logged in user)
    
    if request.method == 'POST':
        # Get material details before deletion for message
        material_name = job_material.material.name
        quantity = job_material.quantity
        unit = job_material.material.unit_of_measurement
        
        # Restore material stock if not a 'returned' record
        if job_material.result != 'returned':
            material = job_material.material
            material.current_stock += job_material.quantity
            material.save(update_fields=['current_stock'])
        
        # Delete the record
        job_material.delete()
        
        # Update job financial summary
        job.create_financial_summary()
        
        messages.success(
            request, 
            f"Removed {quantity} {unit} of {material_name} from job. "
            f"Stock has been restored to inventory."
        )
        
        return redirect('workshop_app:job_detail', job_id=job.job_id)
    
    context = {
        'job_material': job_material,
        'job': job,
    }
    
    return render(request, 'workshop_app/jobs/material_confirm_delete.html', context)

@login_required
def job_material_return(request, material_id):
    """
    Return material from a job back to inventory.
    """
    job_material = get_object_or_404(JobMaterial, id=material_id)
    job = job_material.job
    
    # Check if already returned
    if job_material.result == 'returned':
        messages.warning(request, "This material has already been returned to inventory.")
        return redirect('workshop_app:job_detail', job_id=job.job_id)
    
    if request.method == 'POST':
        # Get return quantity from form
        try:
            return_quantity = float(request.POST.get('return_quantity', 0))
        except ValueError:
            return_quantity = 0
        
        if return_quantity <= 0:
            messages.error(request, "Return quantity must be greater than zero.")
            return redirect('workshop_app:job_detail', job_id=job.job_id)
        
        if return_quantity > job_material.quantity:
            messages.error(
                request, 
                f"Cannot return more than {job_material.quantity} {job_material.material.unit_of_measurement}."
            )
            return redirect('workshop_app:job_detail', job_id=job.job_id)
        
        # Record the return
        job_material.return_to_inventory(return_quantity)
        
        messages.success(
            request, 
            f"Returned {return_quantity} {job_material.material.unit_of_measurement} "
            f"of {job_material.material.name} to inventory."
        )
        
        return redirect('workshop_app:job_detail', job_id=job.job_id)
    
    context = {
        'job_material': job_material,
        'job': job,
    }
    
    return render(request, 'workshop_app/jobs/material_return_form.html', context)
