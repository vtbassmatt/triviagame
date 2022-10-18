from django.db import models
from django.utils.crypto import get_random_string


def generate_passcode():
    return get_random_string(10, 'ABCDEFGHJKLMNPQRTUVWXYZ2346789')


class Game(models.Model):    
    name = models.CharField(max_length=60)
    passcode = models.CharField(max_length=20, default=generate_passcode)
    open = models.BooleanField(default=False)

    def __str__(self):
        return self.name


class Team(models.Model):
    game = models.ForeignKey(Game, on_delete=models.CASCADE)
    name = models.CharField(max_length=200)
    members = models.TextField(blank=True)
    passcode = models.CharField(max_length=20, blank=True)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['game', 'name']
        constraints = [
            models.UniqueConstraint(
                fields=['game', 'name'],
                name='ensure_unique_team_names',
            ),
        ]


class Page(models.Model):
    MYSTERIES = [
        'The mysterious future...',
        'All will be revealed in time.',
        'Wouldn\'t you like to know?',
        'The suspense must be killing you!',
        'It\'s a secret to everybody.',
    ]

    class PageState(models.IntegerChoices):
        LOCKED = 0      # players cannot see the page at all
        OPEN = 1        # players can see and answer the page
        SCORING = 2     # players can see, but not answer, the page

    game = models.ForeignKey(Game, on_delete=models.CASCADE)
    order = models.SmallIntegerField()
    state = models.IntegerField(
        choices=PageState.choices,
        default=PageState.LOCKED,
    )
    title = models.CharField(max_length=100)
    description = models.TextField(blank=True)

    def __str__(self):
        return f"{self.game} :: {self.order}. {self.title}"
    
    class Meta:
        ordering = ['game', 'order']
        constraints = [
            models.UniqueConstraint(
                fields=['game', 'order'],
                name='ensure_page_order',
            ),
        ]
    
    def mystery_description(self):
        index = self.game.id + self.order
        return Page.MYSTERIES[index % len(Page.MYSTERIES)]


class Question(models.Model):
    page = models.ForeignKey(Page, on_delete=models.PROTECT)
    order = models.SmallIntegerField()
    question = models.TextField()
    answer = models.TextField(blank=True)

    def __str__(self):
        return f"{self.order}. {self.question}"

    class Meta:
        ordering = ['page', 'order']
        constraints = [
            models.UniqueConstraint(
                fields=['page', 'order'],
                name='ensure_question_order',
            ),
        ]


class Response(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    team = models.ForeignKey(Team, on_delete=models.CASCADE)
    value = models.CharField(max_length=100)
    graded = models.BooleanField(default=False)
    score = models.SmallIntegerField(default=0)

    def __str__(self):
        return self.value

    class Meta:
        ordering = ['question', 'team']
        constraints = [
            models.UniqueConstraint(
                fields=['question', 'team'],
                name='one_answer_per_team',
            ),
        ]
