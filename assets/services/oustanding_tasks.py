from django.db.models import query
from django.urls import reverse
from urllib.parse import urlencode

def get_equipment_tasks(equipment):
    tasks = []
    query_params = urlencode({'equipmentid':equipment.pk})

    if equipment.requires_software:
        url = reverse( "assets:set_equipment_software")
        full_url = f"{url}?{query_params}"

        tasks.append({
            "type": "software",
            "label": "Add software",
            "url": full_url
        })

    if equipment.asset.requires_configuration:
        url = reverse("assets:set_equipment_configuration")
        full_url = f"{url}?{query_params}"
        tasks.append({
            "type": "configuration",
            "label": "Add configuration",
            "url": full_url
        })
    return tasks
