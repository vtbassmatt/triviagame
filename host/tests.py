from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

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

    def test_password_change_form_has_password_manager_metadata(self):
        self.client.login(username='testhost', password='oldpassword123')
        response = self.client.get(reverse('password_change'))
        content = response.content.decode()
        self.assertRegex(content, r'<input(?=[^>]*name="old_password")(?=[^>]*autocomplete="current-password")[^>]*>')
        self.assertRegex(content, r'<input(?=[^>]*name="new_password1")(?=[^>]*autocomplete="new-password")[^>]*>')
        self.assertRegex(content, r'<input(?=[^>]*name="new_password2")(?=[^>]*autocomplete="new-password")[^>]*>')

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
        self.assertFormError(response, 'form', 'old_password',
                             'Your old password was entered incorrectly. Please enter it again.')

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
