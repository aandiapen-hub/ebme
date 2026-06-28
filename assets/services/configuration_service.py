from model_information.models import EquipmentConfigurationLink
from django.utils import timezone


def apply_configuration_change(equipment, configuration, reason=None):
    # close current installation
    EquipmentConfigurationLink.objects.filter(
        equipment=equipment,
        is_current=True
    ).update(
        is_current=False,
        removed_on=timezone.now().date(),
    )

    # create new installation record
    return EquipmentConfigurationLink.objects.create(
        equipment=equipment,
        configuration=configuration,
        installed_on=timezone.now().date(),
        is_current=True,
        notes=reason or "",
    )
    

