# Monaco embeddable support courtesy of https://github.com/lukasbach/embeddable-monaco
from django.shortcuts import render
from django.views.decorators.clickjacking import xframe_options_sameorigin


def monaco_test(request):
    monaco_options = {
        'code': 'initial_code',
        'lang': 'markdown',
        'minimap': 'false',
        'contextmenu': 'false',
        'lineNumbers': 'off',
        'folding': 'false',
        # 'dontPostValueOnChange': 'true',
    }
    return render(request, 'monaco_test.html', {'monaco_options': monaco_options})


@xframe_options_sameorigin
def monaco_iframe(request):
    return render(request, 'monaco/iframe.html')
