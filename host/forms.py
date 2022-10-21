from django import forms
from game.models import Game, Page, Question
from game.widgets import Bs5TextInput, Bs5Textarea



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
            'description': 'Long description (Markdown allowed)',
        }


class QuestionForm(forms.ModelForm):
    class Meta:
        model = Question
        fields = [
            'question',
            'answer',
        ]
        widgets = {
            'question': Bs5Textarea,
            'answer': Bs5Textarea,
        }
