from django.db import models
from clusters.models import Cluster
from gigachat import GigaChat
from gigachat.exceptions import GigaChatException

class Complaint(models.Model):
    email = models.CharField(max_length=100, default='No Email')
    name = models.CharField(max_length=100, default='Unnamed Complaint')
    text = models.TextField()
    x = models.FloatField(default=0.0)
    y = models.FloatField(default=0.0)
    embedding = models.JSONField(default=None, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    cluster = models.ForeignKey(
        Cluster,
        on_delete=models.CASCADE,
        null=True,
        default=None)

    def call_gigachat_embeddings(self, giga_client):
        """Генерация эмбеддингов с обработкой ошибок"""
        try:
            response = giga_client.embeddings(self.text)
            self.embedding = response.data[0].embedding
        except Exception as e:
            raise GigaChatException(f"Ошибка генерации: {str(e)}")

    def save(self, *args, **kwargs):
        if not self.embedding:
            self.call_gigachat_embeddings(
                GigaChat(
                    credentials=settings.GIGACHAT_TOKEN,
                    verify_ssl_certs=False
                )
            )
        super().save(*args, **kwargs)