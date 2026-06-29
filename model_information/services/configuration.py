
from django.db import transaction
from django.core.exceptions import ValidationError


def create_new_config_version(config):
    scopes = list(config.scopes.all())
    model_links = list(config.model_links.all())
    config.pk = None
    config.version += config.version 
    with transaction.atomic():
        try:
            config.save()
        except Exception as e:
            raise ValidationError(
                {'__all__': str(e)}
            )

        # copy scopes
        for scope in scopes:
            scope.pk = None
            scope.configuration = config
            scope.save()

        # copy model
        for model_link in model_links:
            model_link.pk = None
            model_link.config = config
            model_link.save()

    return config

