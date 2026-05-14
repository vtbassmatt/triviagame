from django.test import TestCase
from django.urls import reverse

from game import models
from game.views import compute_leaderboard_data


class HomeViewTests(TestCase):
    def test_home_clears_team_when_team_and_game_do_not_match(self):
        game_one = models.Game.objects.create(name='Game 1', state=models.Game.GameState.ACCEPTING_TEAMS)
        game_two = models.Game.objects.create(name='Game 2', state=models.Game.GameState.ACCEPTING_TEAMS)
        team = models.Team.objects.create(game=game_two, name='Team 2')

        session = self.client.session
        session['game'] = game_one.id
        session['team'] = team.id
        session.save()

        response = self.client.get(reverse('home'))

        self.assertEqual(response.status_code, 200)
        self.assertIsNone(response.context['team'])
        self.assertEqual(response.context['game'], game_one)
        self.assertNotIn('team', self.client.session)


class ModelPropertyTests(TestCase):
    def test_page_total_points_sums_question_points(self):
        game = models.Game.objects.create(name='Trivia', state=models.Game.GameState.ACCEPTING_TEAMS)
        page = models.Page.objects.create(game=game, order=1, title='Round 1')

        models.Question.objects.create(page=page, order=1, question='Q1', possible_points=2)
        models.Question.objects.create(page=page, order=2, question='Q2', possible_points=3)

        self.assertEqual(page.total_points, 5)


class ComputeLeaderboardDataTests(TestCase):
    def test_compute_leaderboard_sorts_scores_and_ignores_hidden_relocked_pages(self):
        game = models.Game.objects.create(name='Trivia', state=models.Game.GameState.ACCEPTING_TEAMS)
        team_alpha = models.Team.objects.create(game=game, name='Alpha')
        team_beta = models.Team.objects.create(game=game, name='Beta')

        visible_page = models.Page.objects.create(
            game=game,
            order=1,
            title='Visible',
            state=models.Page.PageState.OPEN,
        )
        hidden_relocked_page = models.Page.objects.create(
            game=game,
            order=2,
            title='Hidden',
            is_hidden=True,
            state=models.Page.PageState.LOCKED,
        )

        visible_question = models.Question.objects.create(page=visible_page, order=1, question='Visible Q')
        hidden_question = models.Question.objects.create(page=hidden_relocked_page, order=1, question='Hidden Q')

        models.Response.objects.create(team=team_alpha, question=visible_question, value='a', graded=True, score=5)
        models.Response.objects.create(team=team_beta, question=visible_question, value='b', graded=True, score=3)
        models.Response.objects.create(team=team_alpha, question=hidden_question, value='h', graded=True, score=9)

        rounds, leaderboard, gold_medals = compute_leaderboard_data(game)

        self.assertEqual(rounds, [1, 'total'])
        self.assertEqual(leaderboard, [['Alpha', 5, 5], ['Beta', 3, 3]])
        self.assertEqual(gold_medals, ['Alpha'])

    def test_compute_leaderboard_returns_all_first_place_teams_when_tied(self):
        game = models.Game.objects.create(name='Trivia', state=models.Game.GameState.ACCEPTING_TEAMS)
        team_alpha = models.Team.objects.create(game=game, name='Alpha')
        team_beta = models.Team.objects.create(game=game, name='Beta')
        page = models.Page.objects.create(game=game, order=1, title='Round 1', state=models.Page.PageState.OPEN)
        question = models.Question.objects.create(page=page, order=1, question='Q1')

        models.Response.objects.create(team=team_alpha, question=question, value='a', graded=True, score=4)
        models.Response.objects.create(team=team_beta, question=question, value='b', graded=True, score=4)

        _, _, gold_medals = compute_leaderboard_data(game)

        self.assertEqual(gold_medals, ['Alpha', 'Beta'])
