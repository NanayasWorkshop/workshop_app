from django.urls import path
from django.views.generic import RedirectView
from .views import (
    material_list, material_detail, 
    material_create, material_update, material_delete,
    material_entry_add,
    scanner_view, material_lookup, material_transaction, transaction_success,
    test_view
)

app_name = 'workshop_app'

urlpatterns = [
    # Home page - redirect to test view for now
    path('', RedirectView.as_view(pattern_name='workshop_app:test'), name='home'),
    
    # Test view
    path('test/', test_view, name='test'),
    
    # Material URLs
    path('materials/', material_list, name='material_list'),
    path('materials/create/', material_create, name='material_create'),
    path('materials/<str:material_id>/', material_detail, name='material_detail'),
    path('materials/<str:material_id>/update/', material_update, name='material_update'),
    path('materials/<str:material_id>/delete/', material_delete, name='material_delete'),
    path('materials/<str:material_id>/entry/add/', material_entry_add, name='material_entry_add'),
    
    # Scanner URLs
    path('scanner/', scanner_view, name='scanner'),
    path('api/material-lookup/', material_lookup, name='material_lookup'),
    path('materials/<str:material_id>/transaction/', material_transaction, name='material_transaction'),
    path('transactions/<int:transaction_id>/success/', transaction_success, name='transaction_success'),
]
