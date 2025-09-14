from django.db import models

# Create your models here.#

class ManagerAccount(models.Model):
    userName = models.TextField(unique=True)
    password = models.TextField()  # plain for now (simple). Prefer hashing later.

    class Meta:
        db_table = "manager_account"

    def __str__(self):
        return f"Manager #{self.id} – {self.userName}"
