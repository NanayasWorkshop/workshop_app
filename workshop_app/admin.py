from django.contrib import admin
from .models import (
    MaterialCategory, MaterialType, Material, MaterialEntry, MaterialTransaction,
    MachineType, Machine, Operator, AttachmentType, MaterialAttachment,
    Client, ContactPerson, ClientHistory, Communication, ClientDocument
)

# Material admin classes
class MaterialTypeInline(admin.TabularInline):
    model = MaterialType
    extra = 1

@admin.register(MaterialCategory)
class MaterialCategoryAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'description')
    search_fields = ('code', 'name')
    inlines = [MaterialTypeInline]

@admin.register(MaterialType)
class MaterialTypeAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'category', 'description')
    list_filter = ('category',)
    search_fields = ('code', 'name', 'description')

class MaterialEntryInline(admin.TabularInline):
    model = MaterialEntry
    extra = 1
    fields = ('quantity', 'price_per_unit', 'purchase_date', 'receipt', 'supplier_name')

class MaterialAttachmentInline(admin.TabularInline):
    model = MaterialAttachment
    extra = 1
    fields = ('attachment_type', 'custom_type', 'description', 'file')

@admin.register(Material)
class MaterialAdmin(admin.ModelAdmin):
    list_display = ('material_id', 'serial_number', 'name', 'material_type', 'color', 'current_stock', 
                   'unit_of_measurement', 'price_per_unit', 'location_in_workshop', 'is_low_stock', 'created_by')
    list_filter = ('material_type__category', 'material_type', 'minimum_stock_alert', 'unit_of_measurement')
    search_fields = ('material_id', 'serial_number', 'supplier_sku', 'name', 'supplier_name', 'brand_name')
    readonly_fields = ('qr_code', 'material_id', 'created_by', 'created_at', 'updated_at')
    inlines = [MaterialEntryInline, MaterialAttachmentInline]
    fieldsets = (
        ('Basic Information', {
            'fields': ('material_id', 'serial_number', 'supplier_sku', 'name', 'material_type', 'color', 'dimensions', 'unit_of_measurement')
        }),
        ('Supplier Information', {
            'fields': ('supplier_name', 'brand_name')
        }),
        ('Inventory Management', {
            'fields': ('current_stock', 'minimum_stock_level', 'minimum_stock_alert', 'location_in_workshop')
        }),
        ('Price Information', {
            'fields': ('price_per_unit', 'purchase_date', 'expiration_date')
        }),
        ('Tracking Information', {
            'fields': ('created_by', 'created_at', 'updated_at')
        }),
        ('Additional Information', {
            'fields': ('project_association', 'notes', 'qr_code')
        }),
    )
    
    def save_model(self, request, obj, form, change):
        if not change:  # Only set created_by for new objects
            obj.created_by = request.user
        super().save_model(request, obj, form, change)

@admin.register(MaterialEntry)
class MaterialEntryAdmin(admin.ModelAdmin):
    list_display = ('id', 'material', 'quantity', 'price_per_unit', 'purchase_date', 'supplier_name')
    list_filter = ('purchase_date', 'supplier_name')
    search_fields = ('material__material_id', 'material__name', 'supplier_name', 'notes')
    date_hierarchy = 'purchase_date'

@admin.register(MaterialTransaction)
class MaterialTransactionAdmin(admin.ModelAdmin):
    list_display = ('id', 'material', 'quantity', 'transaction_type', 'transaction_date', 'operator_name', 'job_reference')
    list_filter = ('transaction_type', 'transaction_date')
    search_fields = ('material__material_id', 'material__name', 'job_reference', 'operator_name', 'notes')
    date_hierarchy = 'transaction_date'

@admin.register(AttachmentType)
class AttachmentTypeAdmin(admin.ModelAdmin):
    list_display = ('id', 'name')
    search_fields = ('name',)

@admin.register(MaterialAttachment)
class MaterialAttachmentAdmin(admin.ModelAdmin):
    list_display = ('id', 'material', 'get_type_display', 'description', 'uploaded_by', 'upload_date')
    list_filter = ('attachment_type', 'upload_date')
    search_fields = ('material__material_id', 'material__name', 'description', 'custom_type')
    date_hierarchy = 'upload_date'
    
    def get_type_display(self, obj):
        return obj.get_type_display()
    get_type_display.short_description = 'Type'

# Machine admin classes
@admin.register(MachineType)
class MachineTypeAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'description')
    search_fields = ('code', 'name')

@admin.register(Machine)
class MachineAdmin(admin.ModelAdmin):
    list_display = ('machine_id', 'name', 'machine_type', 'status', 'location_in_workshop', 'hourly_rate')
    list_filter = ('machine_type', 'status')
    search_fields = ('machine_id', 'name', 'manufacturer', 'model_number', 'serial_number')
    readonly_fields = ('qr_code',)
    fieldsets = (
        ('Basic Information', {
            'fields': ('machine_id', 'name', 'machine_type', 'manufacturer', 'model_number', 
                      'serial_number', 'location_in_workshop')
        }),
        ('Purchase Information', {
            'fields': ('purchase_date', 'purchase_price', 'supplier', 'warranty_end_date')
        }),
        ('Technical Specifications', {
            'fields': ('working_area', 'power_requirements', 'maximum_work_speed', 'precision')
        }),
        ('Operational Costs', {
            'fields': ('hourly_rate', 'setup_time', 'setup_rate', 'cleanup_time', 'cleanup_rate')
        }),
        ('Status', {
            'fields': ('status', 'reserved_until')  # Removed current_job
        }),
        ('QR Code', {
            'fields': ('qr_code',)
        }),
    )

# Operator admin class
@admin.register(Operator)
class OperatorAdmin(admin.ModelAdmin):
    list_display = ('operator_id', 'user', 'specialization', 'skill_level', 'hourly_rate')
    list_filter = ('skill_level',)
    search_fields = ('operator_id', 'user__username', 'user__first_name', 'user__last_name', 'specialization')
    filter_horizontal = ('certified_machines',)
    fieldsets = (
        ('Basic Information', {
            'fields': ('operator_id', 'user', 'specialization', 'skill_level')
        }),
        ('Financial Information', {
            'fields': ('hourly_rate', 'productivity_factor')
        }),
        ('Skills & Certifications', {
            'fields': ('certified_machines', 'special_skills')
        }),
    )

# Client admin classes
class ContactPersonInline(admin.TabularInline):
    model = ContactPerson
    extra = 1

class ClientDocumentInline(admin.TabularInline):
    model = ClientDocument
    extra = 1

class CommunicationInline(admin.TabularInline):
    model = Communication
    extra = 1
    fields = ('date', 'comm_type', 'contact_person', 'staff_member', 'summary', 'follow_up_required', 'follow_up_date')

@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = ('client_id', 'name', 'type', 'status', 'primary_email', 'phone_number', 'city', 'country')
    list_filter = ('status', 'type', 'country')
    search_fields = ('client_id', 'name', 'primary_email', 'industry')
    readonly_fields = ('client_id', 'created_date', 'last_updated')
    inlines = [ContactPersonInline, ClientDocumentInline]
    fieldsets = (
        ('Basic Information', {
            'fields': ('client_id', 'name', 'type', 'industry', 'reference_source', 'status', 'notes')
        }),
        ('Contact Information', {
            'fields': ('primary_email', 'secondary_email', 'phone_number', 'mobile_number', 'website', 'social_media')
        }),
        ('Address', {
            'fields': ('street_address', 'address_line_2', 'city', 'state_province', 'postal_code', 'country')
        }),
        ('Financial Information', {
            'fields': ('tax_id', 'payment_terms', 'currency', 'discount_rate', 'credit_limit', 'account_status')
        }),
        ('System Information', {
            'fields': ('created_date', 'last_updated')
        }),
    )

@admin.register(ClientHistory)
class ClientHistoryAdmin(admin.ModelAdmin):
    list_display = ('client', 'projects_completed', 'total_spending', 'average_project_value', 'latest_project_date')
    inlines = [CommunicationInline]
    readonly_fields = ('average_project_value',)

@admin.register(ContactPerson)
class ContactPersonAdmin(admin.ModelAdmin):
    list_display = ('name', 'client', 'position', 'department', 'primary_contact', 'direct_email', 'phone')
    list_filter = ('primary_contact', 'client')
    search_fields = ('name', 'client__name', 'position', 'direct_email')

@admin.register(Communication)
class CommunicationAdmin(admin.ModelAdmin):
    list_display = ('date', 'client_name', 'comm_type', 'contact_person', 'staff_member', 'summary', 'follow_up_required')
    list_filter = ('comm_type', 'follow_up_required', 'date')
    search_fields = ('summary', 'client_history__client__name', 'contact_person__name')
    date_hierarchy = 'date'
    
    def client_name(self, obj):
        return obj.client_history.client.name
    client_name.short_description = 'Client'

@admin.register(ClientDocument)
class ClientDocumentAdmin(admin.ModelAdmin):
    list_display = ('title', 'client', 'doc_type', 'upload_date', 'expiration_date')
    list_filter = ('doc_type', 'upload_date')
    search_fields = ('title', 'client__name', 'notes', 'tags')
    date_hierarchy = 'upload_date'
