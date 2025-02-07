from django.db import models

class Complaint(models.Model):
    email = models.CharField(max_length=100, default='No Email')
    name = models.CharField(max_length=100, default='Unnamed Complaint')
    text = models.TextField()
    x = models.IntegerField(default=0)
    y = models.IntegerField(default=0)
    cluster = models.CharField(max_length=100, default='Unnamed Cluster')
    embedding = models.TextField()