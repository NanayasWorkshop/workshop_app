from django.urls import path
from django.views.generic import RedirectView
from .views import (
    material_list, material_detail, 
    material_create, material_update, material_delete,
    material_entry_add, material_attachment_delete,
    material_attachment_view, material_attachment_download,
    scanner_view, material_lookup,
    machine_list, machine_detail,
    machine_create, machine_update, machine_delete,
    machine_status_update,
    machine_usage_add, machine_usage_success,
    machine_maintenance_add, machine_consumable_add,
    machine_usage_list, maintenance_list, machine_usage_report,
    client_list, client_detail,
    client_create, client_update, client_delete,
    contact_create, contact_update, contact_delete,
    communication_add, document_delete,
    # New job views
    job_list, job_detail, job_create, job_update, job_delete,
    job_status_change, job_milestone_add, job_milestone_update,
    job_scanner_view, job_lookup, job_activate, job_deactivate,
    job_material_add, job_material_delete, job_material_return,
    job_machine_add, job_machine_end, job_machine_list,
    job_financial_summary, job_report,
    # Existing
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
    
    # Material Scanner URLs - just keep scanner and lookup
    path('scanner/', scanner_view, name='scanner'),
    path('api/material-lookup/', material_lookup, name='material_lookup'),
    
    # Machine URLs
    path('machines/', machine_list, name='machine_list'),
    path('machines/create/', machine_create, name='machine_create'),
    
    # Machine Reports URLs
    path('machines/usage/list/', machine_usage_list, name='machine_usage_list'),
    path('machines/maintenance/list/', maintenance_list, name='maintenance_list'),
    path('machines/usage/report/', machine_usage_report, name='machine_usage_report'),
    
    # Machine detail and other machine-specific URLs
    path('machines/<str:machine_id>/', machine_detail, name='machine_detail'),
    path('machines/<str:machine_id>/update/', machine_update, name='machine_update'),
    path('machines/<str:machine_id>/delete/', machine_delete, name='machine_delete'),
    path('machines/<str:machine_id>/status/', machine_status_update, name='machine_status_update'),
    path('machines/<str:machine_id>/usage/add/', machine_usage_add, name='machine_usage_add'),
    path('machines/usage/<int:usage_id>/success/', machine_usage_success, name='machine_usage_success'),
    path('machines/<str:machine_id>/maintenance/add/', machine_maintenance_add, name='machine_maintenance_add'),
    path('machines/<str:machine_id>/consumable/add/', machine_consumable_add, name='machine_consumable_add'),
    
    # Job URLs
    path('jobs/', job_list, name='job_list'),
    path('jobs/create/', job_create, name='job_create'),
    
    # Job Scanner URLs - IMPORTANT: These must come BEFORE the job_detail URL
    path('jobs/scanner/', job_scanner_view, name='job_scanner_view'),
    path('api/job-lookup/', job_lookup, name='job_lookup'),
    path('jobs/deactivate/', job_deactivate, name='job_deactivate'),
    
    # Job detail and other job-specific URLs
    path('jobs/<str:job_id>/', job_detail, name='job_detail'),
    path('jobs/<str:job_id>/update/', job_update, name='job_update'),
    path('jobs/<str:job_id>/delete/', job_delete, name='job_delete'),
    path('jobs/<str:job_id>/status/', job_status_change, name='job_status_change'),
    path('jobs/<str:job_id>/activate/', job_activate, name='job_activate'),
    path('jobs/<str:job_id>/milestone/add/', job_milestone_add, name='job_milestone_add'),
    path('jobs/milestone/<int:milestone_id>/update/', job_milestone_update, name='job_milestone_update'),
    
    # Job Material URLs
    path('jobs/<str:job_id>/material/add/', job_material_add, name='job_material_add'),
    path('jobs/material/<int:material_id>/delete/', job_material_delete, name='job_material_delete'),
    path('jobs/material/<int:material_id>/return/', job_material_return, name='job_material_return'),
    path('jobs/material/add/', job_material_add, name='job_material_add_active'),  # For active job
    
    # Job Machine URLs
    path('jobs/<str:job_id>/machine/add/', job_machine_add, name='job_machine_add'),
    path('jobs/<str:job_id>/machine/<str:machine_id>/add/', job_machine_add, name='job_machine_add_specific'),
    path('jobs/machine/<int:usage_id>/end/', job_machine_end, name='job_machine_end'),
    path('jobs/<str:job_id>/machines/', job_machine_list, name='job_machine_list'),
    path('jobs/machine/add/', job_machine_add, name='job_machine_add_active'),  # For active job
    
    # Job Financial URLs
    path('jobs/<str:job_id>/financials/', job_financial_summary, name='job_financial_summary'),
    path('jobs/<str:job_id>/report/', job_report, name='job_report'),
    
    # Client URLs
    path('clients/', client_list, name='client_list'),
    path('clients/create/', client_create, name='client_create'),
    path('clients/<str:client_id>/', client_detail, name='client_detail'),
    path('clients/<str:client_id>/update/', client_update, name='client_update'),
    path('clients/<str:client_id>/delete/', client_delete, name='client_delete'),
    path('clients/<str:client_id>/contact/add/', contact_create, name='contact_create'),
    path('contacts/<int:contact_id>/update/', contact_update, name='contact_update'),
    path('contacts/<int:contact_id>/delete/', contact_delete, name='contact_delete'),
    path('clients/<str:client_id>/communication/add/', communication_add, name='communication_add'),
    path('documents/<int:document_id>/delete/', document_delete, name='document_delete'),
]
