import json
from django.http import HttpResponse

def add_htmx_message(
    response: type[HttpResponse],
    message_level: str,
    message: str
):

    response["HX-Trigger"] = json.dumps({
            "show_message": {
                "message": message,
                "level": message_level,
            },
        })
    return response
    
