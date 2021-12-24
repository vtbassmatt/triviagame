from django import forms


class SomePageForm(forms.Form):
    page = forms.IntegerField(widget=forms.HiddenInput)
