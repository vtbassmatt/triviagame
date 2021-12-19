from django import forms

from .models import Team
from .widgets import Bs5TextInput, Bs5NumberInput, Bs5Textarea


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
    )

    class Meta:
        model = Team
        fields = ('name', 'members')
        widgets = {
            'name': Bs5TextInput,
            'members': Bs5Textarea,
        }
        labels = {
            'name': 'Team name',
            'members': 'Team members',
        }


class ReJoinTeamForm(forms.Form):
    id = forms.IntegerField(label="Team ID", widget=Bs5NumberInput)
    code = forms.CharField(label="Code", max_length=20, widget=Bs5TextInput)


class CsrfDummyForm(forms.Form):
    pass
