from django.db import models

class Account(models.Model):
    userName = models.TextField()
    password = models.TextField()

    class Meta:
        db_table = "account"

    def __str__(self):
        return f"Message #{self.id}"
