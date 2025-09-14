from django import forms
from website.models import Account
from rooms.models import Classroom, Reservation

class AccountForm(forms.ModelForm):
    class Meta:
        model = Account
        fields = ["userName", "password"]

class ClassroomForm(forms.ModelForm):
    class Meta:
        model = Classroom
        fields = ["roomnumber", "roomsize", "roomcapacity", "start_time", "stop_time", "status"]

class ReservationForm(forms.ModelForm):
    class Meta:
        model = Reservation
        # Works whether Reservation.user is TextField or ForeignKey(Account)
        fields = ["user", "roomnumber", "roomsize", "time", "date"]

from django import forms

class ManagerLoginForm(forms.Form):
    userName = forms.CharField(max_length=150)
    password = forms.CharField(widget=forms.PasswordInput)