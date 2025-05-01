from .material_views import (
    material_list, material_detail, 
    material_create, material_update, material_delete,
    material_entry_add, material_attachment_delete
)
from .attachment_views import (
    material_attachment_view, material_attachment_download
)
from .scanner_views import (
    scanner_view, material_lookup, material_transaction,
    transaction_success
)
from .machine_views import (
    machine_list, machine_detail,
    machine_create, machine_update, machine_delete,
    machine_status_update,
    machine_usage_add, machine_usage_success,
    machine_maintenance_add, machine_consumable_add
)
from .machine_scanner_views import (
    machine_scanner_view, machine_lookup,
    quick_usage_start, quick_usage_end,
    quick_maintenance_report
)
from .test_view import test_view
from .user_views import profile_view
from .dashboard_view import dashboard_view

# This allows importing views directly from the views module
