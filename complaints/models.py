from django.db import models
from clusters.models import Cluster

class Complaint(models.Model):
    email = models.CharField(max_length=100, default='No Email')
    name = models.CharField(max_length=100, default='Unnamed Complaint')
    text = models.TextField()
    x = models.IntegerField(default=0)
    y = models.IntegerField(default=0)
    embedding = models.JSONField(default=None, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    cluster = models.ForeignKey(
        Cluster,
        on_delete=models.CASCADE,
        null=True,
        default=None
    )
