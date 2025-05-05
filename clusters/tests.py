from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from .models import Cluster
from complaints.models import Complaint
from projects.models import Project
from unittest.mock import patch, MagicMock
from gigachat.exceptions import GigaChatException


class ClustersAPITests(TestCase):
    def setUp(self):
        # Create test project
        self.project = Project.objects.create()
        
        # Create test cluster
        self.cluster = Cluster.objects.create(
            name="Test Cluster",
            summary="Test cluster summary",
            model="TestModel",
            project=self.project,
            size=2
        )
        
        # Create test complaints associated with the cluster
        self.complaint1 = Complaint.objects.create(
            email="test1@example.com",
            name="Test Complaint 1",
            text="This is a test complaint 1",
            project=self.project,
            cluster=self.cluster
        )
        
        self.complaint2 = Complaint.objects.create(
            email="test2@example.com",
            name="Test Complaint 2",
            text="This is a test complaint 2",
            project=self.project,
            cluster=self.cluster
        )
        
        # Create API client
        self.client = APIClient()

    def test_get_all_clusters(self):
        """Test getting list of clusters"""
        url = reverse('cluster-list-create', kwargs={'project_id': self.project.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['name'], "Test Cluster")

    def test_create_cluster(self):
        """Test creating a new cluster"""
        url = reverse('cluster-list-create', kwargs={'project_id': self.project.id})
        data = {
            'name': 'New Cluster',
            'summary': 'New cluster summary',
            'model': 'NewModel',
            'project': self.project.id,
            'size': 0
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Cluster.objects.count(), 2)
        self.assertEqual(response.data['name'], 'New Cluster')

    def test_get_cluster_detail(self):
        """Test getting cluster details"""
        url = reverse('cluster-detail', kwargs={
            'project_id': self.project.id,
            'cluster_id': self.cluster.id
        })
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], "Test Cluster")
        self.assertEqual(len(response.data['complaints']), 2)
        
        # Verify complaints data
        complaints = response.data['complaints']
        self.assertEqual(complaints[0]['name'], "Test Complaint 1")
        self.assertEqual(complaints[1]['name'], "Test Complaint 2")

    def test_create_cluster_with_complaints(self):
        """Test creating a cluster with complaints"""
        url = reverse('create-cluster', kwargs={'project_id': self.project.id})
        data = {
            'complaint_ids': [self.complaint1.id, self.complaint2.id],
            'model': 'TestModel'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Verify new cluster was created
        new_cluster_id = response.data['cluster_id']
        new_cluster = Cluster.objects.get(id=new_cluster_id)
        self.assertEqual(new_cluster.size, 2)
        
        # Verify complaints were assigned to the new cluster
        self.assertEqual(
            Complaint.objects.filter(cluster_id=new_cluster_id).count(), 
            2
        )

    @patch('clusters.models.call_gigachat')
    @patch('clusters.models.call_openrouter')
    def test_generate_summary(self, mock_openrouter, mock_gigachat):
        """Test cluster summary generation with mocked LLM API calls"""
        # Setup mock return values
        mock_gigachat.side_effect = ["Test Cluster Name", "This is a mocked summary for testing purposes"]
        mock_openrouter.return_value = "OpenRouter summary for testing"
        
        # Test GigaChat model
        result = self.cluster.generate_summary("GigaChat")
        self.assertEqual(result, ("Test Cluster Name", "This is a mocked summary for testing purposes"))
        self.assertEqual(mock_gigachat.call_count, 2)  # Called once for name, once for summary
        
        # Reset mock
        mock_gigachat.reset_mock()
        
        # Test other model (OpenRouter)
        result = self.cluster.generate_summary("Other")
        self.assertEqual(result, "OpenRouter summary for testing")
        mock_openrouter.assert_called_once()
        self.assertEqual(mock_gigachat.call_count, 0)

    # @patch('clusters.models.call_gigachat')
    # def test_generate_summary_errors(self, mock_gigachat):
    #     """Test error handling in cluster summary generation"""
    #     # Test GigaChat exception
    #     mock_gigachat.side_effect = GigaChatException("API Error")
    #     result = self.cluster.generate_summary("GigaChat")
    #     self.assertEqual(result, "Не удалось сгенерировать описание")
    #
    #     # Test general exception
    #     mock_gigachat.side_effect = Exception("General Error")
    #     result = self.cluster.generate_summary("GigaChat")
    #     self.assertEqual(result, "Ошибка генерации описания")
    #
    #     # Test empty cluster (no complaints)
    #     with patch('complaints.models.Complaint.objects.filter') as mock_filter:
    #         mock_filter.return_value.exists.return_value = False
    #         result = self.cluster.generate_summary("GigaChat")
    #         self.assertEqual(result, "Нет жалоб для анализа")