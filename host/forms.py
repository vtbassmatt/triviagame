from django import forms
from django.contrib.auth import get_user_model

from game.models import Game, Page, Question, Team
from game.widgets import (
    Bs5TextInput,
    Bs5NumberInput,
    Bs5Textarea,
    Bs5Select,
)


User = get_user_model()


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


class GameHostForm(forms.Form):
    host = forms.ModelChoiceField(
        None,
        required=True,
        label="Add additional host",
        widget=Bs5Select,
    )

    def __init__(self, data=None, queryset=None, *args, **kwargs):
        super().__init__(data, *args, **kwargs)
        self.fields['host'].queryset = queryset


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
            'description': 'Long description (Markdown allowed)',
        }


class QuestionForm(forms.ModelForm):
    class Meta:
        model = Question
        fields = [
            'question',
            'answer',
            'possible_points',
        ]
        widgets = {
            'question': Bs5Textarea,
            'answer': Bs5Textarea,
            'possible_points': Bs5NumberInput,
        }
        labels = {
            'question': 'Question (Markdown allowed)',
            'answer': 'Answer (Markdown allowed)',
        }


class TeamForm(forms.Form):
    name = forms.CharField(
        label='Team name',
        max_length=200,
        widget=Bs5TextInput(attrs={
            'autocomplete': 'off',
            'data-1p-ignore': True,
        }),
    )
    members = forms.CharField(
        label='Team members (display only, no required format)',
        max_length=200,
        required=False,
        widget=Bs5TextInput(attrs={
            'autocomplete': 'off',
        }),
    )
