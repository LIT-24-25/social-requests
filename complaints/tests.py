from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from complaints.models import Complaint
from projects.models import Project


class ComplaintsAPITests(TestCase):
    def setUp(self):
        # Создаем тестовый проект (без поля name)
        self.project = Project.objects.create(id=1)

        # Создаем тестовые жалобы
        self.complaint1 = Complaint.objects.create(
            email="test1@example.com",
            name="Test Complaint 1",
            text="This is a test complaint 1",
            project=self.project
        )

        self.complaint2 = Complaint.objects.create(
            email="test2@example.com",
            name="Test Complaint 2",
            text="This is a test complaint 2",
            project=self.project
        )

        # Создаем тестовый клиент API
        self.client = APIClient()

    def test_get_all_complaints(self):
        """Тест получения списка всех жалоб через API"""
        # Используем URL 'complaints/' из вашего urls.py с project_id
        url = reverse('complaint-list-create', kwargs={'project_id': self.project.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

    def test_create_complaint(self):
        """Тест создания новой жалобы через API"""
        url = reverse('complaint-list-create', kwargs={'project_id': self.project.id})
        data = {
            'email': 'new@example.com',
            'name': 'New API Complaint',
            'text': 'This is a new complaint via API',
            'project': self.project.id
        }

        response = self.client.post(url, data, format='json')

        # Проверяем успешное создание
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Проверяем, что жалоба действительно создалась в БД
        self.assertEqual(Complaint.objects.count(), 3)

        # Проверяем данные созданной жалобы
        new_complaint = Complaint.objects.get(email='new@example.com')
        self.assertEqual(new_complaint.name, 'New API Complaint')
        self.assertEqual(new_complaint.text, 'This is a new complaint via API')
        self.assertEqual(new_complaint.project, self.project)