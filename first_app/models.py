from django.db import models

class Complaint(models.Model):
    name = models.TextField(_MAX_LENGTH = 30)
    text = models.TextField(_MAX_LENGTH = 200)
