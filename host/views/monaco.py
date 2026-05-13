# Monaco embeddable support courtesy of https://github.com/lukasbach/embeddable-monaco
from django.shortcuts import render
from django.views.decorators.clickjacking import xframe_options_sameorigin


@xframe_options_sameorigin
def monaco_iframe(request):
    return render(request, 'monaco/iframe.html')
