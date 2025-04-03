from django.db import models
from gigachat import GigaChat
from gigachat.exceptions import GigaChatException
from .mymodels import call_gigachat, call_qwen
import random


class Cluster(models.Model):
    name = models.CharField(max_length=100, default='Unnamed Cluster')
    summary = models.TextField()
    model = models.CharField(max_length=50, default='GigaChat')  # Field to store which model was used
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def generate_summary(self, model):
        try:
            # Перемещаем импорт внутрь метода для избежания циклической зависимости
            from complaints.models import Complaint

            complaints = Complaint.objects.filter(cluster=self)
            if not complaints.exists():
                return "Нет жалоб для анализа"
            amount = random.randint(10, 30)
            complaints_list = list(complaints)
            complaints_for_summary = random.sample(complaints_list, min(amount, len(complaints_list)))
            complaints_texts = [f"Жалоба {i + 1}: {c.text}" for i, c in enumerate(complaints_for_summary)]

            combined_text = "\n".join(complaints_texts)

            if model == "GigaChat":
                prompt_title = f"""Проанализируй следующие жалобы и создай название на русском языке, 
                        обобщающее основные проблемы и тенденции. Не пиши "Обобщенное название:". Суммарная длина ответа должна быть строго 2-3 слова:

                        {combined_text}
                        """
                prompt_summary = f"""Проанализируй следующие жалобы и создай краткое обобщение на русском языке, содержазее одно предложение. 
                        ВАЖНО: Суммарная длина ответа должна быть строго 10-20 слов:

                        {combined_text}
                        """
                response = call_gigachat(prompt_title, prompt_summary)
            else:
                prompt = f"""Analyse the following complaints and create a brief summary, 
                        highlighting the main problems and trends. Summary should containt 10-20 words:

                        {combined_text}
                        """
                response = call_qwen(prompt)
            return response

        except GigaChatException as e:
            print(f"Ошибка GigaChat: {str(e)}")
            return "Не удалось сгенерировать описание"
        except Exception as e:
            print(f"Общая ошибка: {str(e)}")
            return "Ошибка генерации описания"