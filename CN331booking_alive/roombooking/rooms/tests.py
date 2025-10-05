from django.test import TestCase, Client
from django.urls import reverse
from .models import Classroom, Reservation

ROOMS_URL_NAME = "rooms"
LOGIN_URL_NAME = "login"
MY_RESERVATIONS_URL_NAME = "my_reservations"


def set_session_user(client: Client, user_id: str):
    session = client.session
    session["user_id"] = user_id
    session.save()


class RoomsViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        # Make some classrooms; status "1" means selectable, "0" should be excluded by your view
        Classroom.objects.bulk_create([
            Classroom(roomnumber="S101", roomsize="s", start_time="9",  stop_time="12", status="1"),
            Classroom(roomnumber="S102", roomsize="s", start_time="9",  stop_time="12", status="0"),  # excluded
            Classroom(roomnumber="M201", roomsize="m", start_time="8",  stop_time="10", status="1"),
            Classroom(roomnumber="L301", roomsize="l", start_time="10", stop_time="12", status="1"),
        ])

    def test_redirects_to_login_when_not_logged_in(self):
        resp = self.client.get(reverse(ROOMS_URL_NAME))
        # Expect redirect to login
        self.assertEqual(resp.status_code, 302)
        self.assertIn(reverse(LOGIN_URL_NAME), resp.url)

    def test_lists_rooms_excluding_reserved_and_status_zero(self):
        # user "alice" already reserved S101; S102 has status "0" -> both must be excluded
        Reservation.objects.create(user="alice", roomnumber="S101", roomsize="s",
                                   time="10", date="2025-10-06")

        set_session_user(self.client, "alice")
        resp = self.client.get(reverse(ROOMS_URL_NAME))
        self.assertEqual(resp.status_code, 200)

        # Context should only contain rooms not reserved by alice and with status != "0"
        small = list(resp.context.get("smallclassroom", []))
        medium = list(resp.context.get("mediumclassroom", []))
        large = list(resp.context.get("largeclassroom", []))

        # S101 removed because user reserved it; S102 removed because status="0"
        self.assertNotIn("S101", small)
        self.assertNotIn("S102", small)

        # Medium and Large should include what’s available
        self.assertIn("M201", medium)
        self.assertIn("L301", large)

    def test_time_search_computes_remaining_slots_small(self):
        """
        For S101 with start=9 stop=11 and one reservation at time=10 on date,
        remaining should be ['9', '11'] in s_times.
        """
        # Adjust S101 time window just for this test
        c = Classroom.objects.get(roomnumber="S101")
        c.start_time, c.stop_time = "9", "11"
        c.save()

        Reservation.objects.create(user="bob", roomnumber="S101", roomsize="s",
                                   time="10", date="2025-10-06")

        set_session_user(self.client, "alice")
        resp = self.client.post(
            reverse(ROOMS_URL_NAME),
            {
                "button_type": "small_time_search",
                "date": "2025-10-06",
                "classroom": "S101",
            },
        )
        self.assertEqual(resp.status_code, 200)
        self.assertIn("s_times", resp.context)
        self.assertListEqual(sorted(resp.context["s_times"]), ["11", "9"])

    def test_create_reservation_small_submit_redirects(self):
        set_session_user(self.client, "alice")
        resp = self.client.post(
            reverse(ROOMS_URL_NAME),
            {
                "submit_type": "small_submit",
                "date": "2025-10-07",
                "classroom": "S101",
                "time": "10",
            },
        )
        # Should redirect back to rooms after creating
        self.assertEqual(resp.status_code, 302)
        self.assertIn(reverse(ROOMS_URL_NAME), resp.url)

        # Verify it exists
        self.assertTrue(
            Reservation.objects.filter(
                user="alice", roomnumber="S101", roomsize="s", date="2025-10-07", time="10"
            ).exists()
        )


class MyReservationsViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        Classroom.objects.create(roomnumber="S101", roomsize="s", start_time="9", stop_time="12", status="1")
        Classroom.objects.create(roomnumber="M201", roomsize="m", start_time="9", stop_time="12", status="1")

        # Seed reservations for two users
        self.r1 = Reservation.objects.create(user="alice", roomnumber="S101", roomsize="s",
                                             time="10", date="2025-10-06")
        self.r2 = Reservation.objects.create(user="bob",   roomnumber="M201", roomsize="m",
                                             time="09", date="2025-10-06")

    def test_redirects_to_login_when_not_logged_in(self):
        resp = self.client.get(reverse(MY_RESERVATIONS_URL_NAME))
        self.assertEqual(resp.status_code, 302)
        self.assertIn(reverse(LOGIN_URL_NAME), resp.url)

    def test_lists_only_current_users_reservations(self):
        set_session_user(self.client, "alice")
        resp = self.client.get(reverse(MY_RESERVATIONS_URL_NAME))
        self.assertEqual(resp.status_code, 200)

        reservations = list(resp.context.get("reservations", []))
        # Only alice's reservation should show up
        self.assertEqual(len(reservations), 1)
        self.assertEqual(reservations[0].id, self.r1.id)

    def test_cancel_deletes_only_own_reservation(self):
        # Bob logs in and tries to delete Alice's reservation -> your view only deletes when id + user match
        set_session_user(self.client, "bob")
        resp = self.client.post(reverse(MY_RESERVATIONS_URL_NAME), {"rid": str(self.r1.id)})
        self.assertEqual(resp.status_code, 302)  # redirected back

        # Alice's reservation should still exist
        self.assertTrue(Reservation.objects.filter(id=self.r1.id).exists())

        # Bob deletes his own reservation
        resp = self.client.post(reverse(MY_RESERVATIONS_URL_NAME), {"rid": str(self.r2.id)})
        self.assertEqual(resp.status_code, 302)
        self.assertFalse(Reservation.objects.filter(id=self.r2.id).exists())

class RoomsEdgeCaseTests(TestCase):
    def setUp(self):
        self.client = Client()
        # Large room used for time search tests
        Classroom.objects.create(
            roomnumber="L301", roomsize="l", start_time="10", stop_time="12", status="1"
        )

    def test_large_time_search_sets_l_times_and_renders(self):
        """
        With start=10, stop=12 and an existing reservation at 11 on that date,
        remaining times should be ['10','12'] and appear under ctx['l_times'].
        """
        set_session_user(self.client, "alice")
        Reservation.objects.create(
            user="bob", roomnumber="L301", roomsize="l", time="11", date="2025-10-08"
        )

        resp = self.client.post(
            reverse(ROOMS_URL_NAME),
            {
                "button_type": "large_time_search",
                "date": "2025-10-08",
                "classroom": "L301",
            },
        )
        self.assertEqual(resp.status_code, 200)
        self.assertIn("l_times", resp.context)
        self.assertCountEqual(resp.context["l_times"], ["10", "12"])

    def test_submit_missing_fields_rerenders_and_does_not_create(self):
        """
        When any of (user_id, date, classroom, time) is missing, view should re-render
        rooms.html (200) and not create a Reservation.
        We'll omit 'time' to simulate the user not picking a slot.
        """
        set_session_user(self.client, "alice")
        before = Reservation.objects.count()

        resp = self.client.post(
            reverse(ROOMS_URL_NAME),
            {
                "submit_type": "large_submit",
                "date": "2025-10-09",
                "classroom": "L301",
                # "time": missing on purpose
            },
        )
        self.assertEqual(resp.status_code, 200)  # re-render, not redirect
        self.assertEqual(Reservation.objects.count(), before)

    def test_large_submit_success_creates_roomsize_l(self):
        """
        Full, valid submission for a large room should redirect and create
        Reservation with roomsize='l'.
        """
        set_session_user(self.client, "alice")
        resp = self.client.post(
            reverse(ROOMS_URL_NAME),
            {
                "submit_type": "large_submit",
                "date": "2025-10-10",
                "classroom": "L301",
                "time": "10",
            },
        )
        self.assertEqual(resp.status_code, 302)  # redirect back to rooms
        self.assertTrue(
            Reservation.objects.filter(
                user="alice",
                roomnumber="L301",
                roomsize="l",
                date="2025-10-10",
                time="10",
            ).exists()
        )
