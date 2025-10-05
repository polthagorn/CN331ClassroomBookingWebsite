from django.test import TestCase, Client
from django.urls import reverse
import unittest
from .models import Account

# Create your tests here.


class SimpleMathTest(TestCase):  # Check that 2 + 2 equals 4 (sanity test).
    def test_addition(self):

        self.assertEqual(2 + 2, 4)


class SignupCreateAccountTest(unittest.TestCase):  # Check account creation.
    def setUp(self):
        self.client = Client()

    def test_signup_success_creates_account(self):
        resp = self.client.post(
            reverse("login"),
            {
                "submit_type": "signup",
                "signup_username": "new_user_1",
                "signup_password": "password123",
            },
        )
        self.assertEqual(resp.status_code, 302)  # redirects back to login
        # account exists
        self.assertTrue(Account.objects.filter(userName="new_user_1").exists())
        # get flash message
        resp2 = self.client.get(reverse("login"))
        self.assertEqual(resp2.context["username_created"], "Account created.")


class SignupRejectUsernameTest(TestCase):  # Check rejecting bad username.
    def setUp(self):
        self.client = Client()

    def test_signup_username_with_space_rejected(self):
        resp = self.client.post(
            reverse("login"),
            {
                "submit_type": "signup",
                "signup_username": "bad user",
                "signup_password": "password123",
            },
        )
        self.assertEqual(resp.status_code, 302)
        resp2 = self.client.get(reverse("login"))
        self.assertEqual(
            resp2.context["user_name_error"], "Usernames cannot contain spaces."
        )


class SignupRejectPasswordTest(TestCase):  # Check rejecting bad password.
    def setUp(self):
        self.client = Client()

    def test_signup_too_short_password_rejected(self):
        resp = self.client.post(
            reverse("login"),
            {
                "submit_type": "signup",
                "signup_username": "gooduser",
                "signup_password": "short",
            },
        )
        self.assertEqual(resp.status_code, 302)
        resp2 = self.client.get(reverse("login"))
        self.assertEqual(
            resp2.context["password_length_error"],
            "Password must be at least 8 characters.",
        )


class LoginSuccessTest(TestCase):  # Check login success.
    def setUp(self):
        self.client = Client()
        self.acc = Account.objects.create(userName="loginuser", password="secret123")

    def test_login_success_redirects_to_rooms_and_sets_session(self):
        resp = self.client.post(
            reverse("login"),
            {
                "submit_type": "login",
                "login_username": "loginuser",
                "login_password": "secret123",
            },
        )
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(resp["Location"], reverse("rooms"))
        self.assertEqual(self.client.session.get("user_id"), self.acc.id)


class LoginWrongPasswordTest(TestCase):  # Check if input wrong password.
    def setUp(self):
        self.client = Client()
        Account.objects.create(userName="wrongpass", password="rightpass")

    def test_login_wrong_password_sets_error(self):
        resp = self.client.post(
            reverse("login"),
            {
                "submit_type": "login",
                "login_username": "wrongpass",
                "login_password": "badpass",
            },
        )
        self.assertEqual(resp.status_code, 302)
        resp2 = self.client.get(reverse("login"))
        self.assertEqual(resp2.context["password_error"], "Incorrect password.")


class LoginNonExistentUserTest(TestCase):  # Check if  input wrong username.
    def setUp(self):
        self.client = Client()

    def test_login_nonexistent_user_sets_error(self):
        resp = self.client.post(
            reverse("login"),
            {
                "submit_type": "login",
                "login_username": "idontexist",
                "login_password": "anything",
            },
        )
        self.assertEqual(resp.status_code, 302)
        resp2 = self.client.get(reverse("login"))
        self.assertEqual(
            resp2.context["user_name_error"],
            "That account doesn’t exist. Please sign up.",
        )


class ProfileLoginRequiredTest(TestCase):  # Check that page redirect if not logged in.
    def setUp(self):
        self.client = Client()

    def test_profile_redirects_if_not_logged_in(self):
        resp = self.client.get(reverse("profile"))
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(resp["Location"], reverse("login"))


class ProfileShowUsernameTest(TestCase):  # Check if username showed correctly
    def setUp(self):
        self.client = Client()
        self.acc = Account.objects.create(userName="profileuser", password="pass123")
        s = self.client.session
        s["user_id"] = self.acc.id
        s.save()

    def test_profile_loads_username(self):
        resp = self.client.get(reverse("profile"))
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.context["username"], "profileuser")


class ProfileLogoutTest(TestCase):  # Check if user logged out correctly.
    def setUp(self):
        self.client = Client()
        self.acc = Account.objects.create(userName="logoutuser", password="pass123")
        s = self.client.session
        s["user_id"] = self.acc.id
        s.save()

    def test_logout_clears_session_and_redirects(self):
        resp = self.client.post(reverse("profile"), {"logout": "logoutconfirm"})
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(resp["Location"], reverse("rooms"))
        self.assertIsNone(self.client.session.get("user_id"))

if __name__ == "__main__":
    unittest.main()
