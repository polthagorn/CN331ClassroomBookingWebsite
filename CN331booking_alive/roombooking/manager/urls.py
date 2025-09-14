# manager/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path("login/", views.manager_login, name="manager_login"),
    path("logout/", views.manager_logout, name="manager_logout"),

    path("", views.dashboard, name="manager_dashboard"),

    path("account/create/", views.account_create, name="account_create"),
    path("classroom/create/", views.classroom_create, name="classroom_create"),
    path("reservation/create/", views.reservation_create, name="reservation_create"),

    path("account/<int:pk>/edit/", views.account_edit, name="account_edit"),
    path("classroom/<int:pk>/edit/", views.classroom_edit, name="classroom_edit"),
    path("reservation/<int:pk>/edit/", views.reservation_edit, name="reservation_edit"),

    path("account/<int:pk>/delete/", views.account_delete, name="account_delete"),
    path("classroom/<int:pk>/delete/", views.classroom_delete, name="classroom_delete"),
    path("reservation/<int:pk>/delete/", views.reservation_delete, name="reservation_delete"),
]
