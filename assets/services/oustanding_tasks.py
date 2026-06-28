from django.db.models import query
from django.urls import reverse
from urllib.parse import urlencode

def get_equipment_tasks(equipment):
    tasks = []

    if equipment.requires_software:
        url = reverse( "assets:set_equipment_software")
        query_params = urlencode({'equipmentid':equipment.pk})
        full_url = f"{url}?{query_params}"

        tasks.append({
            "type": "software",
            "label": "Add software",
            "url": full_url
        })
    '''
    if equipment.requires_configuration:
        tasks.append({
            "type": "configuration",
            "label": "Add configuration",
            "url": reverse("equipment_config", args=[equipment.pk]),
        })
    '''
    return tasks
