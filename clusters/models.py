from django.db import models

class Cluster(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    summary = models.TextField()

    def __str__(self):
        return str(self.id) + ' ' + self.summary