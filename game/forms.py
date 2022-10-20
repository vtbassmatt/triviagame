from django import forms

from .models import Team
from .widgets import Bs5TextInput, Bs5NumberInput


class JoinGameForm(forms.Form):
    id = forms.IntegerField(label="Game ID", widget=Bs5NumberInput)
    code = forms.CharField(label="Code", max_length=20, widget=Bs5TextInput)


class CreateTeamForm(forms.ModelForm):
    TEAM_NAME_IDEAS = (
        "Win, Booze, or Draw",
        "Red Hot Trivia Peppers",
        "The Smartinis",
        "The Scranton Stranglers",
        "Harry, You're a Quizard",
        "I Can't Feel My Mace When I'm Windu",
        "Walt Quizney World",
        "Bears, Beets, Battlestar Galactica",
        "Dame Agatha Quiztie",
        "Alternative Facts",
        "Air of Truthiness",
        "Les Quizerables",
        "John Trivialta",
        "Risky Quizness",
        "Trivia Newton John",
        "Quizteama Aguilera",
        "Just Google It",
    )

    class Meta:
        model = Team
        fields = ('name', 'members')
        widgets = {
            'name': Bs5TextInput,
            'members': Bs5TextInput,
        }
        labels = {
            'name': 'Team name',
            'members': 'Team members (for display only, separate with spaces, commas, or whatever you want)',
        }


class ReJoinTeamForm(forms.Form):
    id = forms.IntegerField(label="Team ID", widget=Bs5NumberInput)
    code = forms.CharField(label="Code", max_length=20, widget=Bs5TextInput)
