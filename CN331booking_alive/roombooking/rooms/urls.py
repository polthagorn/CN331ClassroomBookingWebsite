from django.urls import path
from . import views

urlpatterns = [
    path("rooms/", views.rooms, name="rooms"),
    path("my-reservations/", views.my_reservations, name="my_reservations"),
]
