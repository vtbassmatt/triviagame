import random

from django import forms

from .widgets import Bs5TextInput, Bs5NumberInput, Bs5Textarea, Bs5RadioSelect


class JoinGameForm(forms.Form):
    id = forms.IntegerField(label="Game ID", widget=Bs5NumberInput)
    code = forms.CharField(label="Code", max_length=20, widget=Bs5TextInput)


class CreateTeamForm(forms.Form):
    TEAM_NAME_CHOICES = (
        ("Win, Booze, or Draw", "Win, Booze, or Draw"),
        ("Red Hot Trivia Peppers", "Red Hot Trivia Peppers"),
        ("The Smartinis", "The Smartinis"),
        ("The Scranton Stranglers", "The Scranton Stranglers"),
        ("Harry, You're a Quizard", "Harry, You're a Quizard"),
        ("I Can't Feel My Mace When I'm Windu", "I Can't Feel My Mace When I'm Windu"),
        ("Walt Quizney World", "Walt Quizney World"),
        ("Bears, Beets, Battlestar Galactica", "Bears, Beets, Battlestar Galactica"),
        ("Dame Agatha Quiztie", "Dame Agatha Quiztie"),
    )

    #name = forms.CharField(label='Team name', max_length=200, widget=Bs5TextInput)
    name = forms.ChoiceField(
        label='Team name',
        # team names will be shuffled in __init__, but have to be here for
        # validation to pass
        choices=TEAM_NAME_CHOICES,
        widget=Bs5RadioSelect,
    )
    members = forms.CharField(label='Team members', widget=Bs5Textarea)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['name'].widget.choices = random.sample(
            CreateTeamForm.TEAM_NAME_CHOICES,
            k=len(CreateTeamForm.TEAM_NAME_CHOICES),
        )


class ReJoinTeamForm(forms.Form):
    id = forms.IntegerField(label="Team ID", widget=Bs5NumberInput)
    code = forms.CharField(label="Code", max_length=20, widget=Bs5TextInput)


class CsrfDummyForm(forms.Form):
    pass
