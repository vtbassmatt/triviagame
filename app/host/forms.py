from django import forms

from triviagame.widgets import Bs5TextInput, Bs5NumberInput


class HostGameForm(forms.Form):
    id = forms.IntegerField(label="Game ID", widget=Bs5NumberInput)
    code = forms.CharField(label="Host Key", max_length=40, widget=Bs5TextInput)


class SomePageForm(forms.Form):
    page = forms.IntegerField(widget=forms.HiddenInput)
