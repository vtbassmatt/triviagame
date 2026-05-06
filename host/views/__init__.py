from host.views.host import *
from host.views.editor import *


from django.shortcuts import render

def monaco_test(request):
    return render(request, 'monaco_test.html')
