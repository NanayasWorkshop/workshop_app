from django.contrib import admin
from .models import (
    MaterialCategory, MaterialType, Material, MaterialEntry,
    MachineType, Machine,
    Operator
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

@admin.register(Material)
class MaterialAdmin(admin.ModelAdmin):
    list_display = ('material_id', 'serial_number', 'name', 'material_type', 'current_stock', 
                   'unit_of_measurement', 'price_per_unit', 'location_in_workshop', 'is_low_stock')
    list_filter = ('material_type', 'minimum_stock_alert', 'unit_of_measurement')
    search_fields = ('material_id', 'serial_number', 'name', 'supplier_name', 'brand_name')
    readonly_fields = ('qr_code',)
    inlines = [MaterialEntryInline]
    fieldsets = (
        ('Basic Information', {
            'fields': ('material_id', 'serial_number', 'name', 'material_type', 'color', 'dimensions', 'unit_of_measurement')
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
        ('Additional Information', {
            'fields': ('project_association', 'notes', 'qr_code')
        }),
    )

@admin.register(MaterialEntry)
class MaterialEntryAdmin(admin.ModelAdmin):
    list_display = ('id', 'material', 'quantity', 'price_per_unit', 'purchase_date', 'supplier_name')
    list_filter = ('purchase_date', 'supplier_name')
    search_fields = ('material__material_id', 'material__name', 'supplier_name', 'notes')
    date_hierarchy = 'purchase_date'

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
