from .material_views import (
    material_list, material_detail, 
    material_create, material_update, material_delete,
    material_entry_add
)
from .scanner_views import (
    scanner_view, material_lookup, material_transaction,
    transaction_success
)
from .test_view import test_view

# This allows importing views directly from the views module
