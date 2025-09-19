# manager/views.py
from functools import wraps

from django.views.decorators.http import require_POST
from django.http import HttpResponseForbidden
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.views.decorators.http import require_http_methods

from website.models import Account            # adjust if your Account model lives elsewhere
from rooms.models import Classroom, Reservation
from .forms import (
    AccountForm,
    ClassroomForm,
    ReservationForm,
    ManagerLoginForm,
)
from .models import ManagerAccount


# -----------------------
# Auth guard decorator
# -----------------------
def require_manager(view_fn):
    @wraps(view_fn)
    def _wrapped(request, *args, **kwargs):
        if not request.session.get("manager_id"):
            return redirect("manager_login")
        return view_fn(request, *args, **kwargs)
    return _wrapped


# -----------------------
# Auth views
# -----------------------
@require_http_methods(["GET", "POST"])
def manager_login(request):
    if request.session.get("manager_id"):
        return redirect("manager_dashboard")

    form = ManagerLoginForm(request.POST or None)
    msg = ""
    if request.method == "POST":
        if form.is_valid():
            userName = form.cleaned_data["userName"]
            password = form.cleaned_data["password"]
            try:
                mgr = ManagerAccount.objects.get(userName=userName, password=password)
            except ManagerAccount.DoesNotExist:
                mgr = None

            if mgr:
                request.session["manager_id"] = mgr.id
                request.session["manager_name"] = mgr.userName
                return redirect("manager_dashboard")
            else:
                msg = "Invalid credentials."
        else:
            msg = "Please correct the form."

    return render(request, "manager/login.html", {"form": form, "msg": msg})


@require_http_methods(["POST"])
def manager_logout(request):
    request.session.pop("manager_id", None)
    request.session.pop("manager_name", None)
    return redirect("manager_login")


# -----------------------
# Dashboard (overview)
# -----------------------
@require_manager
@require_http_methods(["GET"])
def dashboard(request):
    ctx = {
        "manager_name": request.session.get("manager_name"),
        "accounts": Account.objects.all().order_by("id"),
        "classrooms": Classroom.objects.all().order_by("roomnumber"),
        "reservations": Reservation.objects.all().order_by("-id"),
        "account_form": AccountForm(),
        "classroom_form": ClassroomForm(),
        "reservation_form": ReservationForm(),
    }
    return render(request, "manager/dashboard.html", ctx)


# -----------------------
# Account CRUD
# -----------------------
@require_manager
@require_http_methods(["POST"])
def account_create(request):
    form = AccountForm(request.POST)
    if form.is_valid():
        form.save()
        return redirect("manager_dashboard")

    # On errors, re-render dashboard with form errors
    ctx = {
        "manager_name": request.session.get("manager_name"),
        "accounts": Account.objects.all().order_by("id"),
        "classrooms": Classroom.objects.all().order_by("roomnumber"),
        "reservations": Reservation.objects.all().order_by("-id"),
        "account_form": form,
        "classroom_form": ClassroomForm(),
        "reservation_form": ReservationForm(),
    }
    return render(request, "manager/dashboard.html", ctx)


@require_manager
@require_http_methods(["GET", "POST"])
def account_edit(request, pk):
    acc = get_object_or_404(Account, pk=pk)
    if request.method == "POST":
        form = AccountForm(request.POST, instance=acc)
        if form.is_valid():
            form.save()
            return redirect("manager_dashboard")
    else:
        form = AccountForm(instance=acc)
    # ใช้หน้าแก้ไขรวม (มีฟอร์ม+ปุ่ม Save/Back)
    return render(request, "manager/edit_generic.html", {
        "title": "Edit Account",
        "form": form,
    })



@require_manager
@require_http_methods(["POST"])
def account_delete(request, pk):
    acc = get_object_or_404(Account, pk=pk)
    acc.delete()
    return redirect("manager_dashboard")


# -----------------------
# Classroom CRUD
# -----------------------
@require_manager
@require_http_methods(["POST"])
def classroom_create(request):
    form = ClassroomForm(request.POST)
    if form.is_valid():
        form.save()
        return redirect("manager_dashboard")

    ctx = {
        "manager_name": request.session.get("manager_name"),
        "accounts": Account.objects.all().order_by("id"),
        "classrooms": Classroom.objects.all().order_by("roomnumber"),
        "reservations": Reservation.objects.all().order_by("-id"),
        "account_form": AccountForm(),
        "classroom_form": form,
        "reservation_form": ReservationForm(),
    }
    return render(request, "manager/dashboard.html", ctx)


@require_manager
@require_http_methods(["GET", "POST"])
def classroom_edit(request, pk):
    room = get_object_or_404(Classroom, pk=pk)
    if request.method == "POST":
        form = ClassroomForm(request.POST, instance=room)
        if form.is_valid():
            form.save()
            return redirect("manager_dashboard")
    else:
        form = ClassroomForm(instance=room)
    return render(request, "manager/edit_generic.html", {
        "title": "Edit Classroom",
        "form": form,
    })


@require_manager
@require_http_methods(["POST"])
def classroom_delete(request, pk):
    room = get_object_or_404(Classroom, pk=pk)
    room.delete()
    return redirect("manager_dashboard")


# -----------------------
# Reservation CRUD
# -----------------------
@require_manager
@require_http_methods(["POST"])
def reservation_create(request):
    form = ReservationForm(request.POST)
    if form.is_valid():
        form.save()
        return redirect("manager_dashboard")

    ctx = {
        "manager_name": request.session.get("manager_name"),
        "accounts": Account.objects.all().order_by("id"),
        "classrooms": Classroom.objects.all().order_by("roomnumber"),
        "reservations": Reservation.objects.all().order_by("-id"),
        "account_form": AccountForm(),
        "classroom_form": ClassroomForm(),
        "reservation_form": form,
    }
    return render(request, "manager/dashboard.html", ctx)


@require_manager
@require_http_methods(["GET", "POST"])
def reservation_edit(request, pk):
    res = get_object_or_404(Reservation, pk=pk)
    if request.method == "POST":
        form = ReservationForm(request.POST, instance=res)
        if form.is_valid():
            form.save()
            return redirect("manager_dashboard")
    else:
        form = ReservationForm(instance=res)
    return render(request, "manager/edit_generic.html", {
        "title": "Edit Reservation",
        "form": form,
    })


@require_manager
@require_http_methods(["POST"])
def reservation_delete(request, pk):
    res = get_object_or_404(Reservation, pk=pk)
    res.delete()
    return redirect("manager_dashboard")


# -----------------------
# Optional: forbid GET on deletes
# -----------------------
@require_manager
@require_http_methods(["GET"])
def forbid_delete_get(request):
    return HttpResponseForbidden("Delete must be POST.")


@require_POST
def classroom_toggle(request, pk):
    room = get_object_or_404(Classroom, pk=pk)
    s = f"{room.status}"            # รองรับทั้ง '1'/'0' หรือค่าที่ cast เป็นสตริง
    room.status = "0" if s == "1" else "1"
    room.save(update_fields=["status"])
    return redirect(request.META.get("HTTP_REFERER", "manager_dashboard"))