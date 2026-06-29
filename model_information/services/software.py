

from django.db import transaction
from django.core.exceptions import ValidationError


def add_new_software_version(software, new_version):
    compatible_models = list(software.compatible_models.all())
    software.pk = None
    software.version = new_version 
    software.version_number += software.version_number
    with transaction.atomic():
        try:
            software.save()
        except Exception as e:
            raise ValidationError(
                {'__all__': str(e)}
            )

        # copy scopes
        for model_link in compatible_models :
            model_link.pk = None
            model_link.software = software
            model_link.save()
            

    return software
