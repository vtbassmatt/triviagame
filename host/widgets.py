from django.forms import widgets


class MonacoEditor(widgets.TextInput):
    template_name = "monaco/widget.html"

    class Media:
        js = ['monaco/widget/monaco.js']
