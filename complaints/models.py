from django.db import models
from clusters.models import Cluster
from gigachat import GigaChat
from gigachat.exceptions import GigaChatException
from django.conf import settings

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

    def call_gigachat_embeddings(self, text):
        try:
            # Проверяем, что text не пустой
            if not text or not isinstance(text, str):
                raise ValueError("Text must be a non-empty string")
            
            response = self.gigachat.embeddings(
                model="Embeddings",
                input=text  # Убедитесь, что text - это непустая строка
            )
            return response
        except Exception as e:
            raise GigaChatException(f"Ошибка генерации: {str(e)}")

    def save(self, *args, **kwargs):
        if not self.embedding:
            try:
                # Инициализируем GigaChat с токеном
                gigachat = GigaChat(credentials=settings.GIGACHAT_API_KEY)
                
                # Получаем эмбеддинги
                response = gigachat.embeddings(
                    model="Embeddings",
                    input=self.text
                )
                self.embedding = response
            except Exception as e:
                print(f"Ошибка при получении эмбеддингов: {str(e)}")
                # Временно сохраняем без эмбеддингов
                self.embedding = None
        
        super().save(*args, **kwargs)