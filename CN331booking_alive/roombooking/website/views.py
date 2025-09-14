from django.shortcuts import render,redirect
from .models import Account
from django.http import HttpResponse
import sqlite3
# Create your views here.
from django.shortcuts import render, redirect
from .models import Account

from django.shortcuts import render, redirect
from .models import Account

def profile(request):
    ctx = {}

    # --- Must be logged in (safe: no KeyError) ---
    user_id = request.session.get("user_id")
    if not user_id:
        request.session["changing_username_message"] = "You must log in first."
        return redirect("login")

    # --- Flash message (show once) ---
    flash = request.session.pop("changing_username_message", "")
    if flash:
        ctx["changing_username_message"] = flash

    # --- Load account ---
    try:
        acc = Account.objects.get(id=user_id)
    except Account.DoesNotExist:
        ctx["username"] = None
        ctx["changing_username_message"] = "Account not found."
        return render(request, "profile.html", ctx)

    # username field (supports username or userName)
    ctx["username"] = getattr(acc, "username", getattr(acc, "userName", None))
    ctx.setdefault("changing_username_message", "")

    # --- POST actions (logout / change password) ---
    if request.method == "POST":
        # 1) Logout
        if request.POST.get("logout") == "logoutconfirm":
            request.session.flush()
            return redirect("rooms")

        # 2) Change password
        old_pw = request.POST.get("oldpassword", "")
        new_pw = request.POST.get("newpassword", "")

        # validations
        if not old_pw or not new_pw:
            request.session["changing_username_message"] = "Please fill in both fields."
            return redirect("profile")

        if old_pw == new_pw:
            request.session["changing_username_message"] = "New password must be different from current password."
            return redirect("profile")

        if len(new_pw) < 8:
            request.session["changing_username_message"] = "New password must be at least 8 characters."
            return redirect("profile")

        current_stored_pw = getattr(acc, "password", "")
        if old_pw != current_stored_pw:
            request.session["changing_username_message"] = "Current password is incorrect."
            return redirect("profile")

        # save
        setattr(acc, "password", new_pw)
        acc.save(update_fields=["password"])
        request.session["changing_username_message"] = "Password changed."
        return redirect("profile")  # PRG

    # --- GET ---
    return render(request, "profile.html", ctx)

def index(request):
    """
    If no user session -> show loader, then go to login.
    If logged in -> show loader, then go to rooms.
    """
    user_id = request.session.get("user_id")

    # Choose the target URL name
    if user_id is None:
        target = "login"
    else:
        target = "rooms"

    # Render loader page with target
    return render(request, "index.html", {"target": target})

import re

USERNAME_RE = re.compile(r"^[^\s]{1,150}$")  # no spaces, up to 150 chars

def login(request):  # login + register
    if request.method == "POST":
        subtype = (request.POST.get("submit_type") or "").strip().lower()

        # ---- LOGIN ----
        if subtype == "login":
            un = (request.POST.get("login_username") or "").strip()
            pw = (request.POST.get("login_password") or "")

            if not un or not pw:
                request.session["user_name_error"] = "Please enter username and password."
                return redirect("login")

            try:
                acc = Account.objects.get(userName=un)
            except Account.DoesNotExist:
                request.session["user_name_error"] = "That account doesn’t exist. Please sign up."
                return redirect("login")

            if pw == acc.password:
                # store session user id
                request.session["user_id"] = acc.id
                # Optional: make session expire in 7 days (adjust as you like)
                request.session.set_expiry(7 * 24 * 60 * 60)
                return redirect("rooms")
            else:
                request.session["password_error"] = "Incorrect password."
                return redirect("login")

        # ---- SIGNUP ----
        elif subtype == "signup":
            su = (request.POST.get("signup_username") or "").strip()
            sp = (request.POST.get("signup_password") or "")

            # basic checks
            if not su or not sp:
                request.session["user_name_error"] = "Please enter username and password."
                return redirect("login")

            if " " in su:
                request.session["user_name_error"] = "Usernames cannot contain spaces."
                return redirect("login")

            if " " in sp:
                request.session["password_error"] = "Password cannot contain spaces."
                return redirect("login")

            if len(sp) < 8:
                request.session["password_length_error"] = "Password must be at least 8 characters."
                return redirect("login")

            if not USERNAME_RE.match(su):
                request.session["user_name_error"] = "Invalid username."
                return redirect("login")

            if Account.objects.filter(userName=su).exists():
                request.session["username_occupied"] = "This username has already been used."
                return redirect("login")

            Account.objects.create(userName=su, password=sp)
            request.session["username_created"] = "Account created."
            return redirect("login")

        # Unknown subtype → go back
        request.session["user_name_error"] = "Invalid action."
        return redirect("login")

    # GET
    ctx = {
        "password_length_error":   request.session.pop("password_length_error", None),
        "user_name_error":   request.session.pop("user_name_error", None),
        "password_error":    request.session.pop("password_error", None),
        "username_occupied": request.session.pop("username_occupied", None),
        "username_created":  request.session.pop("username_created", None),
    }
    return render(request, "login.html", ctx)
