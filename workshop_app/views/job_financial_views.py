from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum, F, Q
from django.utils import timezone

from ..models import Job, JobFinancial, JobMaterial, JobMachine, JobLabor

@login_required
def job_financial_summary(request, job_id):
    """
    Display financial summary for a job.
    """
    job = get_object_or_404(Job, job_id=job_id)
    
    # Get or create financial record
    try:
        financial = job.financial
    except JobFinancial.DoesNotExist:
        financial = JobFinancial.objects.create(job=job)
    
    # Update with latest costs
    job.create_financial_summary()
    
    # Handle update of quoted amount
    if request.method == 'POST' and 'update_quote' in request.POST:
        try:
            quoted_amount = float(request.POST.get('quoted_amount', 0))
            financial.quoted_amount = quoted_amount
            financial.variance = financial.total_cost - quoted_amount
            financial.save()
            messages.success(request, "Quoted amount updated successfully.")
        except ValueError:
            messages.error(request, "Invalid amount. Please enter a valid number.")
    
    # Handle update of billing status
    elif request.method == 'POST' and 'update_billing' in request.POST:
        status = request.POST.get('billing_status')
        reference = request.POST.get('invoice_reference', '')
        
        try:
            billed_amount = float(request.POST.get('billed_amount', 0))
            financial.billed_amount = billed_amount
            financial.billing_status = status
            financial.invoice_reference = reference
            financial.save()
            financial.update_billing_status()  # Update status based on amount
            messages.success(request, "Billing information updated successfully.")
        except ValueError:
            messages.error(request, "Invalid amount. Please enter a valid number.")
    
    # Get detailed breakdowns
    materials = JobMaterial.objects.filter(job=job).order_by('-date_used')
    machine_usages = JobMachine.objects.filter(job=job).order_by('-start_time')
    labor_entries = JobLabor.objects.filter(job=job).order_by('-date')
    
    # Calculate material costs by category
    material_categories = {}
    for item in materials:
        category = item.material.material_type.category.name
        if category not in material_categories:
            material_categories[category] = {
                'count': 0,
                'cost': 0,
            }
        
        material_categories[category]['count'] += 1
        if item.unit_price:
            material_categories[category]['cost'] += item.quantity * item.unit_price
    
    # Sort by cost (highest first)
    material_categories = dict(
        sorted(material_categories.items(), key=lambda x: x[1]['cost'], reverse=True)
    )
    
    # Calculate machine costs by type
    machine_types = {}
    for usage in machine_usages:
        m_type = usage.machine.machine_type.name
        if m_type not in machine_types:
            machine_types[m_type] = {
                'count': 0,
                'cost': 0,
                'hours': 0,
            }
        
        machine_types[m_type]['count'] += 1
        if usage.total_cost:
            machine_types[m_type]['cost'] += usage.total_cost
        
        if usage.end_time:  # Only count completed sessions
            machine_types[m_type]['hours'] += usage.get_duration_minutes() / 60
    
    # Sort by cost (highest first)
    machine_types = dict(
        sorted(machine_types.items(), key=lambda x: x[1]['cost'], reverse=True)
    )
    
    # Calculate labor costs by type
    labor_types = {}
    for entry in labor_entries:
        l_type = entry.get_labor_type_display()
        if l_type not in labor_types:
            labor_types[l_type] = {
                'count': 0,
                'cost': 0,
                'hours': 0,
            }
        
        labor_types[l_type]['count'] += 1
        cost = entry.hours * entry.hourly_rate
        labor_types[l_type]['cost'] += cost
        labor_types[l_type]['hours'] += entry.hours
    
    # Sort by cost (highest first)
    labor_types = dict(
        sorted(labor_types.items(), key=lambda x: x[1]['cost'], reverse=True)
    )
    
    context = {
        'job': job,
        'financial': financial,
        'material_categories': material_categories,
        'machine_types': machine_types,
        'labor_types': labor_types,
        'materials': materials,
        'machine_usages': machine_usages,
        'labor_entries': labor_entries,
        'now': timezone.now(),
    }
    
    return render(request, 'workshop_app/jobs/financial_summary.html', context)

@login_required
def job_report(request, job_id):
    """
    Generate a detailed job report for invoicing or analysis.
    """
    job = get_object_or_404(Job, job_id=job_id)
    
    # Get financial summary
    try:
        financial = job.financial
    except JobFinancial.DoesNotExist:
        financial = JobFinancial.objects.create(job=job)
    
    # Update with latest costs
    job.create_financial_summary()
    
    # Get detailed breakdowns
    materials = JobMaterial.objects.filter(job=job).order_by('-date_used')
    machine_usages = JobMachine.objects.filter(job=job).order_by('-start_time')
    labor_entries = JobLabor.objects.filter(job=job).order_by('-date')
    
    # Group materials by date
    materials_by_date = {}
    for item in materials:
        date_key = item.date_used.date()
        if date_key not in materials_by_date:
            materials_by_date[date_key] = []
        
        materials_by_date[date_key].append(item)
    
    # Sort dates (newest first)
    materials_by_date = dict(
        sorted(materials_by_date.items(), key=lambda x: x[0], reverse=True)
    )
    
    # Group machine usages by date
    machines_by_date = {}
    for usage in machine_usages:
        date_key = usage.start_time.date()
        if date_key not in machines_by_date:
            machines_by_date[date_key] = []
        
        machines_by_date[date_key].append(usage)
    
    # Sort dates (newest first)
    machines_by_date = dict(
        sorted(machines_by_date.items(), key=lambda x: x[0], reverse=True)
    )
    
    # Group labor by date
    labor_by_date = {}
    for entry in labor_entries:
        date_key = entry.date
        if date_key not in labor_by_date:
            labor_by_date[date_key] = []
        
        labor_by_date[date_key].append(entry)
    
    # Sort dates (newest first)
    labor_by_date = dict(
        sorted(labor_by_date.items(), key=lambda x: x[0], reverse=True)
    )
    
    context = {
        'job': job,
        'financial': financial,
        'materials_by_date': materials_by_date,
        'machines_by_date': machines_by_date,
        'labor_by_date': labor_by_date,
        'materials': materials,
        'machine_usages': machine_usages,
        'labor_entries': labor_entries,
        'report_date': timezone.now(),
    }
    
    return render(request, 'workshop_app/jobs/report.html', context)
