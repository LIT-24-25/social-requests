from django.db import models
from clusters.models import Cluster
from gigachat import GigaChat
from gigachat.exceptions import GigaChatException
from clusters.instances import gigachat_token
from typing import List, Dict, Tuple
import logging
from tqdm import tqdm

logger = logging.getLogger(__name__)

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

    def call_gigachat_embeddings(self, text, giga_client):
        try:
            # Проверяем, что text не пустой
            if not text or not isinstance(text, str):
                raise ValueError("Text must be a non-empty string")
            
            response = giga_client.embeddings(text)
            self.embedding = response.data[0].embedding
        except Exception as e:
            raise GigaChatException(f"Ошибка генерации: {str(e)}")
    
    @staticmethod
    def batch_process_embeddings(complaints: List['Complaint'], texts: List[str], giga_client) -> List['Complaint']:
        """
        Process embeddings for multiple complaints in a batch.
        
        Args:
            complaints (List[Complaint]): List of complaint objects to process
            texts (List[str]): List of complaint texts for embedding
            giga_client: GigaChat client instance
            
        Returns:
            List[Complaint]: List of processed complaints with embeddings
        """
        if len(complaints) != len(texts):
            raise ValueError("Length of complaints and texts must match")
        
        if not complaints:
            return []
            
        processed_complaints = []

        batch_response = giga_client.embeddings(texts)
        for i, (complaint, text) in enumerate(tqdm(zip(complaints, texts), 
                                              total=len(complaints), 
                                              desc="Processing embeddings", 
                                              unit="complaint")):
            complaint.embedding = batch_response.data[i].embedding
            processed_complaints.append(complaint)
            
        logger.info(f"Batch processed {len(complaints)} complaints for embeddings")
        return processed_complaints

    def save(self, *args, **kwargs):
        if not self.embedding:
            try:
                # Инициализируем GigaChat с токеном
                gigachat = GigaChat(credentials=gigachat_token, verify_ssl_certs=False)
                
                # Получаем эмбеддинги
                response = gigachat.embeddings(self.text)
                self.embedding = response.data[0].embedding
            except Exception as e:
                print(f"Ошибка при получении эмбеддингов: {str(e)}")
                # Временно сохраняем без эмбеддингов
                self.embedding = None
        
        super().save(*args, **kwargs)