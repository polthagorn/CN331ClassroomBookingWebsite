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

class ProfileChangePasswordSuccessTest(TestCase): # Check if user password changing work correctly.
    def setUp(self):
        self.client = Client()
        # make a logged-in user
        self.acc = Account.objects.create(userName="cp_user", password="oldpassword")
        s = self.client.session
        s["user_id"] = self.acc.id
        s.save()

    def test_change_password_success(self):
        resp = self.client.post(reverse("profile"), {
            "oldpassword": "oldpassword",
            "newpassword": "newpassword123",
        })
        # redirects via PRG
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(resp["Location"], reverse("profile"))

        # password updated in DB
        self.acc.refresh_from_db()
        self.assertEqual(self.acc.password, "newpassword123")

        # success flash appears on next GET
        resp2 = self.client.get(reverse("profile"))
        self.assertEqual(resp2.context["changing_username_message"], "Password changed.")

class ProfileAccountNotFoundTest(TestCase):  # check  handling account error.
    def setUp(self):
        self.client = Client()
        # put a non-existent user_id into session
        s = self.client.session
        s["user_id"] = 99999  # id that doesn't exist
        s.save()

    def test_profile_account_not_found_sets_message(self):
        resp = self.client.get(reverse("profile"))
        self.assertEqual(resp.status_code, 200)
        # context should have no username
        self.assertIsNone(resp.context["username"])
        # and should show the not found message
        self.assertEqual(
            resp.context["changing_username_message"],
            "Account not found."

        )

class ProfileChangePasswordMissingFieldsTest(TestCase):
    def setUp(self):
        self.client = Client()
        # create a valid user and log them in
        self.acc = Account.objects.create(userName="missingpwuser", password="oldpassword")
        s = self.client.session
        s["user_id"] = self.acc.id
        s.save()

    def test_change_password_missing_fields(self):
        # send blank old/new passwords
        resp = self.client.post(reverse("profile"), {
            "oldpassword": "",
            "newpassword": ""
        })
        # should redirect back to profile
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(resp["Location"], reverse("profile"))

        # next GET shows correct error message
        resp2 = self.client.get(reverse("profile"))
        self.assertEqual(
            resp2.context["changing_username_message"],
            "Please fill in both fields."
        )

class ProfileChangePasswordSameAsOldTest(TestCase):
    def setUp(self):
        self.client = Client()
        # create user and log in
        self.acc = Account.objects.create(userName="samepwuser", password="oldpassword123")
        s = self.client.session
        s["user_id"] = self.acc.id
        s.save()

    def test_change_password_same_as_old_rejected(self):
        # try to change to same password
        resp = self.client.post(reverse("profile"), {
            "oldpassword": "oldpassword123",
            "newpassword": "oldpassword123"
        })
        # should redirect back to profile
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(resp["Location"], reverse("profile"))

        # next GET should show the correct message
        resp2 = self.client.get(reverse("profile"))
        self.assertEqual(
            resp2.context["changing_username_message"],
            "New password must be different from current password."
        )

class ProfileChangePasswordTooShortTest(TestCase):
    def setUp(self):
        self.client = Client()
        # create user and log them in
        self.acc = Account.objects.create(userName="shortpwuser", password="oldpassword123")
        s = self.client.session
        s["user_id"] = self.acc.id
        s.save()

    def test_change_password_too_short_rejected(self):
        # try to change to a password shorter than 8 chars
        resp = self.client.post(reverse("profile"), {
            "oldpassword": "oldpassword123",
            "newpassword": "short"
        })
        # should redirect back to profile
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(resp["Location"], reverse("profile"))

        # next GET should show the correct error message
        resp2 = self.client.get(reverse("profile"))
        self.assertEqual(
            resp2.context["changing_username_message"],
            "New password must be at least 8 characters."
        )

class ProfileChangePasswordWrongCurrentTest(TestCase):
    def setUp(self):
        self.client = Client()
        # create a user with a known password
        self.acc = Account.objects.create(userName="wrongpwuser", password="correctpw123")
        s = self.client.session
        s["user_id"] = self.acc.id
        s.save()

    def test_change_password_incorrect_current(self):
        # provide a wrong current password
        resp = self.client.post(reverse("profile"), {
            "oldpassword": "WRONGPW",
            "newpassword": "newpassword123"
        })
        # should redirect back to profile
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(resp["Location"], reverse("profile"))

        # next GET should show the correct error message
        resp2 = self.client.get(reverse("profile"))
        self.assertEqual(
            resp2.context["changing_username_message"],
            "Current password is incorrect."
        )

class IndexViewTests(TestCase):
    def setUp(self):
        self.client = Client()

    def test_index_without_session_targets_login(self):
        resp = self.client.get(reverse("index"))
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.context["target"], "login")

    def test_index_with_session_targets_rooms(self):
        # fake a logged-in session
        s = self.client.session
        s["user_id"] = 1
        s.save()

        resp = self.client.get(reverse("index"))
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.context["target"], "rooms")

class LoginEmptyFieldsTest(TestCase):
    def setUp(self):
        self.client = Client()

    def test_login_with_missing_username_and_password(self):
        # Post empty username and password
        resp = self.client.post(reverse("login"), {
            "submit_type": "login",
            "login_username": "",
            "login_password": "",
        })
        # Should redirect back to login
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(resp["Location"], reverse("login"))

        # On next GET, the error message should appear in context
        resp2 = self.client.get(reverse("login"))
        self.assertEqual(
            resp2.context["user_name_error"],
            "Please enter username and password."
        )

class SignupEmptyFieldsTest(TestCase):
    def setUp(self):
        self.client = Client()

    def test_signup_with_missing_username_or_password(self):
        # Try with missing username
        resp = self.client.post(reverse("login"), {
            "submit_type": "signup",
            "signup_username": "",
            "signup_password": "password123",
        })
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(resp["Location"], reverse("login"))

        resp2 = self.client.get(reverse("login"))
        self.assertEqual(
            resp2.context["user_name_error"],
            "Please enter username and password."
        )

        # Try with missing password
        resp = self.client.post(reverse("login"), {
            "submit_type": "signup",
            "signup_username": "newuser",
            "signup_password": "",
        })
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(resp["Location"], reverse("login"))

        resp2 = self.client.get(reverse("login"))
        self.assertEqual(
            resp2.context["user_name_error"],
            "Please enter username and password."
        )

class SignupPasswordWithSpacesTest(TestCase):
    def setUp(self):
        self.client = Client()

    def test_signup_password_with_space_rejected(self):
        resp = self.client.post(reverse("login"), {
            "submit_type": "signup",
            "signup_username": "spaceuser",
            "signup_password": "bad pass",  # contains space
        })
        # should redirect back to login
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(resp["Location"], reverse("login"))

        # check error message
        resp2 = self.client.get(reverse("login"))
        self.assertEqual(
            resp2.context["password_error"],
            "Password cannot contain spaces."
        )

class SignupDuplicateUsernameTest(TestCase):
    def setUp(self):
        self.client = Client()
        # create a user with the username already taken
        Account.objects.create(userName="takenuser", password="somepassword")

    def test_signup_duplicate_username_rejected(self):
        resp = self.client.post(reverse("login"), {
            "submit_type": "signup",
            "signup_username": "takenuser",  # already exists
            "signup_password": "anotherpassword123",
        })
        # should redirect back to login
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(resp["Location"], reverse("login"))

        # next GET should show the duplicate username error
        resp2 = self.client.get(reverse("login"))
        self.assertEqual(
            resp2.context["username_occupied"],
            "This username has already been used."
        )