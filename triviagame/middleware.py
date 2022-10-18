import json
from django.contrib.messages import get_messages
from django.utils.decorators import async_only_middleware

@async_only_middleware
def htmx_message_middleware(get_response):
    async def middleware(request):
        response = await get_response(request)
        if 'HX-Request' in request.headers:
            messages = await _get_messages(request)
            if not messages:
                return response
            
            hx_trigger = await _get_initial_trigger(response)
            
            hx_trigger['messages'] = messages
            response.headers['HX-Trigger'] = json.dumps(hx_trigger)
        
        return response

    return middleware

async def _get_messages(request):
    return [
        {"message": message.message, "tags": message.tags}
        for message in get_messages(request)
    ]

async def _get_initial_trigger(response):
    hx_trigger = response.headers.get("HX-Trigger")
    if hx_trigger is None:
        # no HX-Trigger bubbled up
        return {}
    elif hx_trigger.startswith("{"):
        # HX-Trigger using object syntax
        return json.loads(hx_trigger)
    else:
        # HX-Trigger using string syntax
        return {hx_trigger: True}
