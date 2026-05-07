from django.shortcuts import render
from django.views.decorators.clickjacking import xframe_options_sameorigin


def monaco_test(request):
    return render(request, 'monaco_test.html')


@xframe_options_sameorigin
def monaco_iframe(request):
    return render(request, 'monaco/iframe.html')
