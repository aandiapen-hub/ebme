import json

def add_htmx_message(
    response,
    message_level,
    message
):
    response["HX-Trigger"] = json.dumps({
            "show_message": {
                "message": message,
                "level": message_level,
            },
        })
    return response
    
