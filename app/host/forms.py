from django import forms
from triviagame.models import Game
from triviagame.widgets import Bs5TextInput



class SomePageForm(forms.Form):
    page = forms.IntegerField(widget=forms.HiddenInput)


class GameForm(forms.ModelForm):
    class Meta:
        model = Game
        fields = [
            'name',
        ]
        widgets = {
            'name': Bs5TextInput,
        }
        labels = {
            'name': 'Game name',
        }
