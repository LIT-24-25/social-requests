from django.db import models
from clusters.models import Cluster
from projects.models import Project
from gigachat import GigaChat
from gigachat.exceptions import GigaChatException
from clusters.instances import gigachat_token
from typing import List
import logging

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
    project = models.ForeignKey(
        Project,
        null=False,
        default=1,
        on_delete=models.PROTECT)

    def call_gigachat_embeddings(self, text=None, giga_client=None):
        try:
            # Проверяем, что text не пустой
            if not text or not isinstance(text, str):
                text = self.text
                
            if not text or not isinstance(text, str):
                raise ValueError("Text must be a non-empty string")
            
            # Если клиент не передан, создаем новый экземпляр
            if giga_client is None:
                giga_client = GigaChat(credentials=gigachat_token, verify_ssl_certs=False)
                
            response = giga_client.embeddings(text)
            self.embedding = response.data[0].embedding
            return self.embedding
        except Exception as e:
            logger.error(f"Error generating embeddings: {str(e)}")
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
        for i, (complaint, text) in enumerate(zip(complaints, texts)):
            complaint.embedding = batch_response.data[i].embedding
            processed_complaints.append(complaint)
            
        logger.info(f"Batch processed {len(complaints)} complaints for embeddings")
        return processed_complaints