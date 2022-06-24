from django import forms
from triviagame.models import Game, Page
from triviagame.widgets import Bs5TextInput, Bs5Textarea



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


class PageForm(forms.ModelForm):
    class Meta:
        model = Page
        fields = [
            'title',
            'description',
        ]
        widgets = {
            'title': Bs5TextInput,
            'description': Bs5Textarea,
        }
        labels = {
            'title': 'Page title',
            'description': 'Long description',
        }
