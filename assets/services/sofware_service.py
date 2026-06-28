from model_information.models import EquipmentSoftware
from django.utils import timezone


def apply_software_change(equipment, software, user, reason=None):
    # close current installation
    EquipmentSoftware.objects.filter(
        equipment=equipment,
        is_current=True
    ).update(
        is_current=False,
        removed_on=timezone.now().date(),
    )

    # create new installation record
    return EquipmentSoftware.objects.create(
        equipment=equipment,
        software=software,
        installed_on=timezone.now().date(),
        is_current=True,
        notes=reason or "",
    )
    

