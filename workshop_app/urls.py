from django.urls import path
from django.views.generic import RedirectView
from .views import (
    material_list, material_detail, 
    material_create, material_update, material_delete,
    material_entry_add, material_attachment_delete,
    material_attachment_view, material_attachment_download,
    scanner_view, material_lookup, material_transaction, transaction_success,
    machine_list, machine_detail,
    machine_create, machine_update, machine_delete,
    machine_status_update,
    machine_usage_add, machine_usage_success,
    machine_maintenance_add, machine_consumable_add,
    machine_scanner_view, machine_lookup,
    quick_usage_start, quick_usage_end,
    quick_maintenance_report,
    test_view, profile_view, dashboard_view
)

app_name = 'workshop_app'

urlpatterns = [
    # Home page - redirect to dashboard view
    path('', dashboard_view, name='home'),
    
    # Dashboard view
    path('dashboard/', dashboard_view, name='dashboard'),
    
    # User profile
    path('profile/', profile_view, name='profile'),
    
    # Test view - keeping for backward compatibility
    path('test/', test_view, name='test'),
    
    # Material URLs
    path('materials/', material_list, name='material_list'),
    path('materials/create/', material_create, name='material_create'),
    path('materials/<str:material_id>/', material_detail, name='material_detail'),
    path('materials/<str:material_id>/update/', material_update, name='material_update'),
    path('materials/<str:material_id>/delete/', material_delete, name='material_delete'),
    path('materials/<str:material_id>/entry/add/', material_entry_add, name='material_entry_add'),
    
    # Material Attachment URLs
    path('attachments/<int:attachment_id>/', material_attachment_view, name='material_attachment_view'),
    path('attachments/<int:attachment_id>/download/', material_attachment_download, name='material_attachment_download'),
    path('attachments/<int:attachment_id>/delete/', material_attachment_delete, name='material_attachment_delete'),
    
    # Material Scanner URLs
    path('scanner/', scanner_view, name='scanner'),
    path('api/material-lookup/', material_lookup, name='material_lookup'),
    path('materials/<str:material_id>/transaction/', material_transaction, name='material_transaction'),
    path('transactions/<int:transaction_id>/success/', transaction_success, name='transaction_success'),
    
    # Machine URLs
    path('machines/', machine_list, name='machine_list'),
    path('machines/create/', machine_create, name='machine_create'),
    
    # Machine Scanner URLs - IMPORTANT: These must come BEFORE the machine_detail URL
    path('machines/scanner/', machine_scanner_view, name='machine_scanner'),
    path('api/machine-lookup/', machine_lookup, name='machine_lookup'),
    path('machines/<str:machine_id>/usage/start/', quick_usage_start, name='quick_usage_start'),
    path('machines/<str:machine_id>/usage/end/', quick_usage_end, name='quick_usage_end'),
    path('machines/<str:machine_id>/maintenance/report/', quick_maintenance_report, name='quick_maintenance_report'),
    
    # Machine detail and other machine-specific URLs - THESE MUST COME AFTER machine/scanner/
    path('machines/<str:machine_id>/', machine_detail, name='machine_detail'),
    path('machines/<str:machine_id>/update/', machine_update, name='machine_update'),
    path('machines/<str:machine_id>/delete/', machine_delete, name='machine_delete'),
    path('machines/<str:machine_id>/status/', machine_status_update, name='machine_status_update'),
    path('machines/<str:machine_id>/usage/add/', machine_usage_add, name='machine_usage_add'),
    path('machines/usage/<int:usage_id>/success/', machine_usage_success, name='machine_usage_success'),
    path('machines/<str:machine_id>/maintenance/add/', machine_maintenance_add, name='machine_maintenance_add'),
    path('machines/<str:machine_id>/consumable/add/', machine_consumable_add, name='machine_consumable_add'),
]
