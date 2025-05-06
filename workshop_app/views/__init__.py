from .material_views import (
    material_list, material_detail, 
    material_create, material_update, material_delete,
    material_entry_add, material_attachment_delete
)
from .attachment_views import (
    material_attachment_view, material_attachment_download
)
from .scanner_views import (
    scanner_view, material_lookup
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
from .machine_reports import (
    machine_usage_list, maintenance_list, machine_usage_report
)
from .client_views import (
    client_list, client_detail,
    client_create, client_update, client_delete,
    contact_create, contact_update, contact_delete,
    communication_add, document_delete
)
from .job_views import (
    job_list, job_detail, job_create, job_update, job_delete,
    job_status_change, job_milestone_add, job_milestone_update
)
from .job_scanner_views import (
    job_scanner_view, job_lookup, job_activate, job_deactivate
)
from .job_material_views import (
    job_material_add, job_material_delete, job_material_return
)
from .job_machine_views import (
    job_machine_add, job_machine_end, job_machine_list
)
from .job_financial_views import (
    job_financial_summary, job_report
)
from .test_view import test_view
from .user_views import profile_view
from .dashboard_view import dashboard_view
