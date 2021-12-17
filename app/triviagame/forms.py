from django import forms

from .widgets import Bs5TextInput, Bs5NumberInput, Bs5Textarea


class JoinGameForm(forms.Form):
    id = forms.IntegerField(label="Game ID", widget=Bs5NumberInput)
    code = forms.CharField(label="Code", max_length=20, widget=Bs5TextInput)


class CreateTeamForm(forms.Form):
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

    name = forms.CharField(
        label='Team name',
        max_length=200,
        widget=Bs5TextInput,
    )
    members = forms.CharField(label='Team members', widget=Bs5Textarea)


class ReJoinTeamForm(forms.Form):
    id = forms.IntegerField(label="Team ID", widget=Bs5NumberInput)
    code = forms.CharField(label="Code", max_length=20, widget=Bs5TextInput)


class CsrfDummyForm(forms.Form):
    pass
