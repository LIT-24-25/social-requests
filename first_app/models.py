from django.db import models

class Complaint(models.Model):
    name = models.TextField()
    text = models.TextField()
