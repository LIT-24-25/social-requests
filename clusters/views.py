from clusters.models import Cluster
from complaints.models import Complaint
from rest_framework import generics
from .serializers import ClusterSerializer
from complaints.serializers import ComplaintSerializer
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
import logging

logger = logging.getLogger(__name__)

class ClusterListCreate(generics.ListCreateAPIView):
    serializer_class = ClusterSerializer
    
    def get_queryset(self):
        project_id = self.kwargs.get('project_id')
        logger.info(f"ClusterListCreate.get_queryset called with project_id={project_id}")
        
        if project_id:
            queryset = Cluster.objects.filter(project_id=project_id).order_by("-id")
            logger.info(f"Found {queryset.count()} clusters for project_id={project_id}")
            return queryset
        
        queryset = Cluster.objects.order_by("-id").all()
        logger.info(f"Found {queryset.count()} clusters (all)")
        return queryset
    
    def get_serializer_context(self):
        context = super().get_serializer_context()
        context.update({'view': self})
        return context

class ClusterDetailAPI(APIView):
    def get(self, request, cluster_id, project_id=None):
        logger.info(f"ClusterDetailAPI.get called with cluster_id={cluster_id}, project_id={project_id}")
        # Получаем кластер по ID
        if project_id:
            cluster = get_object_or_404(Cluster, id=cluster_id, project_id=project_id)
            logger.info(f"Found cluster with id={cluster_id}, project_id={project_id}")
        else:
            cluster = get_object_or_404(Cluster, id=cluster_id)
            logger.info(f"Found cluster with id={cluster_id}")

        # Получаем все жалобы, связанные с этим кластером
        complaints = Complaint.objects.filter(cluster=cluster)
        logger.info(f"Found {complaints.count()} complaints for cluster_id={cluster_id}")

        # Создаем контекст для сериализатора с view и kwargs
        serializer_context = {
            'request': request,
            'view': self,
            'kwargs': {'project_id': project_id} if project_id else {}
        }

        # Сериализуем данные с контекстом
        cluster_data = ClusterSerializer(cluster, context=serializer_context).data
        complaints_data = ComplaintSerializer(complaints, many=True, context=serializer_context).data

        # Возвращаем данные
        return Response({
            **cluster_data,
            'complaints': complaints_data,
        }, status=status.HTTP_200_OK)