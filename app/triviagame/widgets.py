from django.forms import widgets


class Bs5TextInput(widgets.TextInput):
    template_name = "django/forms/widgets/bs5_input.html"


class Bs5NumberInput(widgets.NumberInput):
    template_name = "django/forms/widgets/bs5_input.html"


class Bs5Textarea(widgets.Textarea):
    template_name = "django/forms/widgets/bs5_textarea.html"


class Bs5Select(widgets.Select):
    template_name = "django/forms/widgets/bs5_select.html"


class Bs5RadioSelect(widgets.RadioSelect):
    template_name = "django/forms/widgets/bs5_radio.html"
    option_template_name = "django/forms/widgets/bs5_radio_option.html"
