from django.db import models

class Cluster(models.Model):
    name = models.CharField(max_length=100, default='Unnamed Complaint')
    summary = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
