from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q

from ..models import Material, MaterialTransaction
from ..forms import MaterialTransactionForm

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
        # Try to find by material_id or serial_number
        material = Material.objects.get(
            Q(material_id=identifier) | Q(serial_number=identifier)
        )
        
        # Return material details as JSON
        data = {
            'found': True,
            'material_id': material.material_id,
            'serial_number': material.serial_number,
            'name': material.name,
            'type': material.material_type.name,
            'current_stock': float(material.current_stock),
            'unit': material.unit_of_measurement,
            'detail_url': f"/materials/{material.material_id}/",
            'transaction_url': f"/materials/{material.material_id}/transaction/",
        }
        
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

@login_required
def material_transaction(request, material_id):
    """
    Handle material consumption or return after scanning
    """
    # Try to find by material_id or serial_number
    material = get_object_or_404(Material, Q(material_id=material_id) | Q(serial_number=material_id))
    
    # Determine transaction type (consumption or return)
    transaction_type = request.GET.get('type', 'consumption')
    if transaction_type not in ['consumption', 'return']:
        transaction_type = 'consumption'  # Default to consumption
    
    if request.method == 'POST':
        form = MaterialTransactionForm(
            request.POST, 
            material=material, 
            transaction_type=transaction_type
        )
        
        if form.is_valid():
            transaction = form.save()
            
            # Set success message
            action = "consumed" if transaction_type == 'consumption' else "returned to inventory"
            messages.success(
                request, 
                f"Successfully {action} {transaction.quantity} {material.unit_of_measurement} of {material.name}"
            )
            
            # Redirect to success page
            return redirect('workshop_app:transaction_success', transaction_id=transaction.id)
    else:
        # Pre-fill operator name if user has a profile
        initial = {}
        if hasattr(request.user, 'operator'):
            initial['operator_name'] = str(request.user.operator)
            
        form = MaterialTransactionForm(
            material=material, 
            transaction_type=transaction_type,
            initial=initial
        )
    
    context = {
        'material': material,
        'form': form,
        'transaction_type': transaction_type,
        'title': 'Material Consumption' if transaction_type == 'consumption' else 'Material Return',
        'action_verb': 'Use' if transaction_type == 'consumption' else 'Return',
    }
    
    return render(request, 'workshop_app/materials/transaction_form.html', context)

@login_required
def transaction_success(request, transaction_id):
    """
    Show transaction success page with details and next actions
    """
    transaction = get_object_or_404(MaterialTransaction, id=transaction_id)
    
    context = {
        'transaction': transaction,
        'material': transaction.material,
        'title': 'Transaction Complete',
    }
    
    return render(request, 'workshop_app/materials/transaction_success.html', context)
