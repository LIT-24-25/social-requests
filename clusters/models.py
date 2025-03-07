from django.db import models
from gigachat import GigaChat
from gigachat.exceptions import GigaChatException
from django.conf import settings

class Cluster(models.Model):
    name = models.CharField(max_length=100, default='Unnamed Cluster')
    summary = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def generate_summary(self):
        """Генерирует суммаризацию жалоб с помощью GigaChat"""
        try:
            # Перемещаем импорт внутрь метода для избежания циклической зависимости
            from complaints.models import Complaint

            # Получаем все жалобы кластера
            complaints = Complaint.objects.filter(cluster=self)
            if not complaints.exists():
                return "Нет жалоб для анализа"

            # Формируем текст для анализа
            complaints_texts = [f"Жалоба {i+1}: {c.text[:500]}" for i, c in enumerate(complaints)]
            combined_text = "\n".join(complaints_texts[:10])  # Берем первые 10 жалоб чтобы не превысить лимиты

            # Создаем промпт
            prompt = f"""Проанализируй следующие жалобы и создай краткое обобщение на русском языке, 
                       выделив основные проблемы и тенденции:
                       
                       {combined_text}
                       
                       Краткое обобщение (3-5 предложений):"""

            # Вызываем GigaChat API
            with GigaChat(credentials=settings.GIGACHAT_TOKEN, verify_ssl_certs=False) as giga:
                response = giga.chat(prompt)
                return response.choices[0].message.content

        except GigaChatException as e:
            print(f"Ошибка GigaChat: {str(e)}")
            return "Не удалось сгенерировать описание"
        except Exception as e:
            print(f"Общая ошибка: {str(e)}")
            return "Ошибка генерации описания"
