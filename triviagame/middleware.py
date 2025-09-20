import json
from django.contrib.messages import get_messages
from django.http import HttpResponse
from django.utils.decorators import async_only_middleware


# https://docs.djangoproject.com/en/5.0/ref/request-response/#django.http.HttpRequest.get_host
class MultipleProxyMiddleware:
    FORWARDED_FOR_FIELDS = [
        "HTTP_X_FORWARDED_FOR",
        "HTTP_X_FORWARDED_HOST",
        "HTTP_X_FORWARDED_SERVER",
    ]

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        """
        Rewrites the proxy headers so that only the most
        recent proxy is used.
        """
        for field in self.FORWARDED_FOR_FIELDS:
            if field in request.META:
                if "," in request.META[field]:
                    parts = request.META[field].split(",")
                    request.META[field] = parts[-1].strip()
        return self.get_response(request)


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


# h/t to https://medium.com/@jwgarcia003/unlocking-django-debug-toolbar-for-json-responses-an-elegant-solution-8c6c231ba760
# but this is only safe in dev, so don't enable it in production
# class NonHtmlDebugToolbarMiddleware:
#     def __init__(self, get_response):
#         self.get_response = get_response

#     def __call__(self, request):
#         response = self.get_response(request)
#         if request.GET.get('debug') and response['Content-Type'] == 'application/json':
#             content = json.dumps(json.loads(response.content), sort_keys=True, indent=2)
#             response = HttpResponse(f'<!DOCTYPE html><html><body><pre>JSON: {content}</pre></body></html>')
#         return response