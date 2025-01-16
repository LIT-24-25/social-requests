from django.db import models

class Complaint(models.Model):
    name = models.CharField(max_length=100, default='Unnamed Complaint')
    text = models.TextField()
    #embedding = JSONField()