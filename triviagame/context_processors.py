from django.conf import settings


def deployment_details(request):
    return {
        "COMMIT_HASH": settings.COMMIT_HASH,
        "DEPLOY_REF": settings.DEPLOY_REF,
    }
