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
# New job models
from .job import Job, JobStatus, JobMilestone
from .job_material import JobMaterial
from .job_machine import JobMachine
from .job_labor import JobLabor
from .job_financial import JobFinancial
from .staff_settings import StaffSettings

