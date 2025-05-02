from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Count

from ..models import (
    MaterialCategory, MaterialType, Material, 
    MachineType, Machine, Operator,
    MaterialTransaction, MachineUsage,
    Client, ContactPerson
)

@login_required
def dashboard_view(request):
    """
    Main dashboard view that replaces the test view.
    Provides an overview of the workshop system with statistics and recent activities.
    """
    # Material statistics
    materials_count = Material.objects.count()
    categories_count = MaterialCategory.objects.count()
    types_count = MaterialType.objects.count()
    
    # Count low stock materials
    low_stock_count = sum(1 for m in Material.objects.all() if m.is_low_stock())
    
    # Machine statistics
    machines_count = Machine.objects.count()
    active_machines = Machine.objects.filter(status='active').count()
    maintenance_machines = Machine.objects.filter(status='maintenance').count()
    out_of_order_machines = Machine.objects.filter(status='out_of_order').count()
    
    # Client statistics
    clients_count = Client.objects.count()
    active_clients = Client.objects.filter(status='active').count()
    prospect_clients = Client.objects.filter(status='prospect').count()
    
    # Operator count
    operators_count = Operator.objects.count()
    
    # Recent material transactions
    recent_transactions = MaterialTransaction.objects.all().order_by('-transaction_date')[:5]
    
    # Recent machine usage
    recent_usages = MachineUsage.objects.all().order_by('-start_time')[:5]
    
    # Combine all stats
    stats = {
        'materials_count': materials_count,
        'categories_count': categories_count,
        'types_count': types_count,
        'low_stock_count': low_stock_count,
        'machines_count': machines_count,
        'active_machines': active_machines,
        'maintenance_machines': maintenance_machines,
        'out_of_order_machines': out_of_order_machines,
        'clients_count': clients_count,
        'active_clients': active_clients,
        'prospect_clients': prospect_clients,
        'operators_count': operators_count,
    }
    
    context = {
        'stats': stats,
        'recent_transactions': recent_transactions,
        'recent_usages': recent_usages,
    }
    
    return render(request, 'workshop_app/dashboard.html', context)
