from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.test import Client, TestCase
from django.urls import reverse
from guardian.shortcuts import assign_perm

from game import models

User = get_user_model()


class PasswordChangeTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testhost',
            password='oldpassword123',
        )

    def test_password_change_form_requires_login(self):
        response = self.client.get(reverse('password_change'))
        self.assertEqual(response.status_code, 302)
        self.assertIn('/host/auth/login/', response['Location'])

    def test_password_change_form_accessible_when_logged_in(self):
        self.client.login(username='testhost', password='oldpassword123')
        response = self.client.get(reverse('password_change'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'host/password_change_form.html')

    def test_password_change_success(self):
        self.client.login(username='testhost', password='oldpassword123')
        response = self.client.post(reverse('password_change'), {
            'old_password': 'oldpassword123',
            'new_password1': 'brandnewpassword456!',
            'new_password2': 'brandnewpassword456!',
        })
        self.assertRedirects(response, reverse('password_change_done'))
        # Verify new password works
        self.assertTrue(self.client.login(username='testhost', password='brandnewpassword456!'))

    def test_password_change_wrong_old_password(self):
        self.client.login(username='testhost', password='oldpassword123')
        response = self.client.post(reverse('password_change'), {
            'old_password': 'wrongpassword',
            'new_password1': 'brandnewpassword456!',
            'new_password2': 'brandnewpassword456!',
        })
        self.assertEqual(response.status_code, 200)
        self.assertIn(
            'Your old password was entered incorrectly.',
            response.context['form'].errors['old_password'][0],
        )

    def test_password_change_done_accessible_when_logged_in(self):
        self.client.login(username='testhost', password='oldpassword123')
        response = self.client.get(reverse('password_change_done'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'host/password_change_done.html')

    def test_home_contains_change_password_link(self):
        self.client.login(username='testhost', password='oldpassword123')
        response = self.client.get(reverse('host_home'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, reverse('password_change'))


class EditorTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='editor',
            password='editorpass123',
        )
        add_game_perm = Permission.objects.get(codename='add_game')
        self.user.user_permissions.add(add_game_perm)
        self.client.login(username='editor', password='editorpass123')

    def test_new_game_creates_game_and_assigns_host_permissions(self):
        response = self.client.post(reverse('new_game'), {
            'name': 'Editor Test Game',
        })

        game = models.Game.objects.get(name='Editor Test Game')
        self.assertRedirects(response, reverse('edit_game', args=(game.id,)))
        self.assertTrue(self.user.has_perm('game.change_game', game))
        self.assertTrue(self.user.has_perm('game.host_game', game))
        self.assertTrue(self.user.has_perm('game.view_game', game))

    def test_new_page_sets_next_order_value(self):
        game = models.Game.objects.create(name='Page Order Game')
        assign_perm('change_game', self.user, game)
        models.Page.objects.create(game=game, order=1, title='Round 1')

        response = self.client.post(reverse('new_page', args=(game.id,)), {
            'title': 'Round 2',
            'description': 'Next round',
        })

        page = game.page_set.get(order=2)
        self.assertRedirects(response, reverse('edit_page', args=(page.id,)))
        self.assertEqual(page.title, 'Round 2')

    def test_new_question_sets_next_order_value(self):
        game = models.Game.objects.create(name='Question Order Game')
        assign_perm('change_game', self.user, game)
        page = models.Page.objects.create(game=game, order=1, title='Round 1')
        models.Question.objects.create(page=page, order=1, question='Q1')

        response = self.client.post(reverse('new_question', args=(page.id,)), {
            'question': 'Q2',
            'answer': 'A2',
            'possible_points': 3,
        })

        question = page.question_set.get(order=2)
        self.assertRedirects(response, reverse('edit_page', args=(page.id,)))
        self.assertEqual(question.question, 'Q2')


class HostInterfaceTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='hoster',
            password='hostpass123',
        )
        self.client.login(username='hoster', password='hostpass123')

    def test_host_home_only_lists_games_user_can_view(self):
        visible_game = models.Game.objects.create(name='Visible Game')
        hidden_game = models.Game.objects.create(name='Hidden Game')
        assign_perm('view_game', self.user, visible_game)

        response = self.client.get(reverse('host_home'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Visible Game')
        self.assertNotContains(response, 'Hidden Game')

    def test_update_game_state_htmx_updates_state(self):
        game = models.Game.objects.create(name='Host State Game')
        assign_perm('host_game', self.user, game)

        response = self.client.post(
            reverse('update_game_state', args=(game.id, models.Game.GameState.ACCEPTING_TEAMS)),
            HTTP_HX_REQUEST='true',
        )

        game.refresh_from_db()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(game.state, models.Game.GameState.ACCEPTING_TEAMS)

    def test_assign_score_grades_response_when_page_is_scoring(self):
        game = models.Game.objects.create(name='Scoring Game')
        page = models.Page.objects.create(
            game=game,
            order=1,
            title='Round 1',
            state=models.Page.PageState.SCORING,
        )
        question = models.Question.objects.create(page=page, order=1, question='Q1')
        team = models.Team.objects.create(game=game, name='Team')
        response_row = models.Response.objects.create(
            question=question,
            team=team,
            value='Answer',
            graded=False,
            score=0,
        )
        assign_perm('host_game', self.user, game)

        response = self.client.post(
            reverse('assign_score', args=(game.id,)),
            {'response': response_row.id, 'score': '2'},
            HTTP_HX_REQUEST='true',
        )

        response_row.refresh_from_db()
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response_row.graded)
        self.assertEqual(response_row.score, 2)


class GameLifecycleIntegrationTests(TestCase):
    def setUp(self):
        self.host_user = User.objects.create_user(
            username='integration_host',
            password='hostpass123',
        )
        add_game_perm = Permission.objects.get(codename='add_game')
        self.host_user.user_permissions.add(add_game_perm)
        self.host_client = Client()
        self.player_client = Client()
        self.host_client.login(username='integration_host', password='hostpass123')

    def test_lifecycle_from_host_editor_to_player_scoring_and_leaderboard(self):
        create_game = self.host_client.post(reverse('new_game'), {'name': 'Lifecycle Game'})
        self.assertEqual(create_game.status_code, 302)
        game = models.Game.objects.get(name='Lifecycle Game')

        create_page = self.host_client.post(
            reverse('new_page', args=(game.id,)),
            {'title': 'Round 1', 'description': 'Round details'},
        )
        self.assertEqual(create_page.status_code, 302)
        page = game.page_set.get(order=1)

        create_question = self.host_client.post(
            reverse('new_question', args=(page.id,)),
            {'question': 'Ultimate answer?', 'answer': '42', 'possible_points': 2},
        )
        self.assertEqual(create_question.status_code, 302)
        question = page.question_set.get(order=1)

        open_game = self.host_client.post(
            reverse('update_game_state', args=(game.id, models.Game.GameState.ACCEPTING_TEAMS)),
            HTTP_HX_REQUEST='true',
        )
        self.assertEqual(open_game.status_code, 200)
        open_page = self.host_client.post(
            reverse('set_page_state', args=(game.id,)),
            {'page': page.id, 'state': 'OPEN'},
            HTTP_HX_REQUEST='true',
        )
        self.assertEqual(open_page.status_code, 204)

        join_game = self.player_client.post(reverse('join_game'), {
            'id': game.id,
            'code': game.passcode,
        })
        self.assertRedirects(join_game, reverse('create_team'))
        create_team = self.player_client.post(reverse('create_team'), {
            'name': 'Integration Team',
            'members': 'Alice, Bob',
        })
        self.assertRedirects(create_team, reverse('play'))
        team = game.team_set.get(name='Integration Team')

        answer = self.player_client.post(reverse('respond', args=(question.id,)), {
            'response_value': '42',
        })
        self.assertEqual(answer.status_code, 200)
        response_row = models.Response.objects.get(team=team, question=question)
        self.assertEqual(response_row.value, '42')

        scoring_page = self.host_client.post(
            reverse('set_page_state', args=(game.id,)),
            {'page': page.id, 'state': 'SCORING'},
            HTTP_HX_REQUEST='true',
        )
        self.assertEqual(scoring_page.status_code, 204)
        score_response = self.host_client.post(
            reverse('assign_score', args=(game.id,)),
            {'response': response_row.id, 'score': '2'},
            HTTP_HX_REQUEST='true',
        )
        self.assertEqual(score_response.status_code, 200)

        leaderboard = self.player_client.get(reverse('leaderboard'))
        self.assertEqual(leaderboard.status_code, 200)
        self.assertEqual(leaderboard.context['leaderboard'], [['Integration Team', 2, 2]])
        self.assertEqual(leaderboard.context['gold_medals'], ['Integration Team'])
