from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from .models import Cluster
from complaints.models import Complaint
from projects.models import Project


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

    def test_cluster_summary_generation(self):
        """Test cluster summary generation"""
        # Create a new cluster without complaints
        empty_cluster = Cluster.objects.create(
            name="Empty Cluster",
            summary="",
            model="TestModel",
            project=self.project
        )
        
        # Test summary generation for empty cluster
        result = empty_cluster.generate_summary("TestModel")
        self.assertEqual(result, "Нет жалоб для анализа")
        
        # Test summary generation for cluster with complaints
        result = self.cluster.generate_summary("TestModel")
        self.assertTrue(len(result) > 0)
        self.assertIsInstance(result, str)

    def test_update_cluster(self):
        """Test updating cluster details"""
        url = reverse('cluster-detail', kwargs={
            'project_id': self.project.id,
            'cluster_id': self.cluster.id
        })
        data = {
            'name': 'Updated Cluster',
            'summary': 'Updated summary',
            'model': 'UpdatedModel'
        }
        response = self.client.patch(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], 'Updated Cluster')
        self.assertEqual(response.data['summary'], 'Updated summary')
        self.assertEqual(response.data['model'], 'UpdatedModel')

    def test_delete_cluster(self):
        """Test deleting a cluster"""
        url = reverse('cluster-detail', kwargs={
            'project_id': self.project.id,
            'cluster_id': self.cluster.id
        })
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Cluster.objects.count(), 0)
        
        # Verify complaints are not deleted when cluster is deleted
        self.assertEqual(Complaint.objects.count(), 2)
        self.assertIsNone(Complaint.objects.get(id=self.complaint1.id).cluster)
        self.assertIsNone(Complaint.objects.get(id=self.complaint2.id).cluster)

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
