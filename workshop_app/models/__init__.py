from .material import MaterialCategory, MaterialType, Material
from .material_entry import MaterialEntry
from .machine import MachineType, Machine, Job
from .operator import Operator
from .transaction import MaterialTransaction
from .machine_usage import MachineUsage
from .machine_maintenance import MachineMaintenance
from .machine_consumable import MachineConsumable, ConsumableReplacement
from .material_attachment import AttachmentType, MaterialAttachment
from .client import Client, ContactPerson, ClientHistory, Communication, ClientDocument

# This allows using the models directly from the models module
