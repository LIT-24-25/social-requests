from django.db import models
from clusters.models import Cluster
from gigachat import GigaChat
from gigachat.exceptions import GigaChatException
from clusters.instances import gigachat_token

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

    def generate_embedding(self, text=None, giga_client=None, raise_error=False):
        """
        Генерирует эмбеддинг для текста и сохраняет его в модели.
        
        Args:
            text (str, optional): Текст для эмбеддинга. Если None, используется self.text.
            giga_client (GigaChat, optional): Клиент GigaChat. Если None, создается новый.
            raise_error (bool): Нужно ли выбрасывать исключение при ошибке или обрабатывать тихо.
            
        Returns:
            bool: True если эмбеддинг успешно создан, False в случае ошибки.
            
        Raises:
            GigaChatException: Если raise_error=True и произошла ошибка при генерации.
        """
        # Если эмбеддинг уже есть и не передан новый текст, возвращаем успех
        if self.embedding and text is None:
            return True
            
        try:
            # Определяем текст
            text_to_embed = text if text is not None else self.text
            
            # Проверяем валидность текста
            if not text_to_embed or not isinstance(text_to_embed, str):
                raise ValueError("Text must be a non-empty string")
            
            # Определяем клиент
            client = giga_client
            if client is None:
                client = GigaChat(credentials=gigachat_token, verify_ssl_certs=False)
            
            # Получаем эмбеддинги
            response = client.embeddings(text_to_embed)
            self.embedding = response.data[0].embedding
            return True
            
        except Exception as e:
            if raise_error:
                raise GigaChatException(f"Ошибка генерации эмбеддингов: {str(e)}")
            else:
                print(f"Ошибка при получении эмбеддингов: {str(e)}")
                self.embedding = None
                return False
    
    def save(self, *args, **kwargs):
        # Упрощенная функция save, которая только сохраняет модель
        super().save(*args, **kwargs)