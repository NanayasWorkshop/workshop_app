from django.shortcuts import render
from django.http import HttpResponse
from ..models import MaterialCategory, MaterialType, Material, MachineType, Machine, Operator


def test_view(request):
    """
    Simple view to test if everything is working correctly.
    This view provides information about the database status.
    """
    # Get counts for each model
    category_count = MaterialCategory.objects.count()
    material_type_count = MaterialType.objects.count()
    material_count = Material.objects.count()
    machine_type_count = MachineType.objects.count()
    machine_count = Machine.objects.count()
    operator_count = Operator.objects.count()
    
    # Put all info in a context
    context = {
        'database_status': {
            'Material Categories': category_count,
            'Material Types': material_type_count,
            'Materials': material_count,
            'Machine Types': machine_type_count,
            'Machines': machine_count,
            'Operators': operator_count,
        }
    }
    
    return render(request, 'workshop_app/test.html', context)
