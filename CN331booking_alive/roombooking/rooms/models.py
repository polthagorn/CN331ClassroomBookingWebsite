from django.db import models

class Classroom(models.Model):
    roomnumber = models.TextField()
    roomsize = models.TextField()
    roomcapacity = models.TextField(default="0")
    start_time = models.TextField(default="0")
    stop_time = models.TextField(default="0")
    status = models.TextField(default="0")

    class Meta:
        db_table = "classroom"

    def __str__(self):
        return str(self.roomnumber)

class Reservation(models.Model):
    user = models.TextField()
    roomnumber = models.TextField()
    roomsize = models.TextField()
    time = models.TextField()  # O'clock
    date = models.TextField()

    class Meta:
        db_table = "reserve"

    def __str__(self):
        return f"User: {self.user}, Room: {self.roomnumber} ({self.roomsize}), Date: {self.date}, Time: {self.time}"
