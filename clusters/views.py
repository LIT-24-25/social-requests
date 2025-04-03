from clusters.models import Cluster
from complaints.models import Complaint
from rest_framework import generics
from .serializers import ClusterSerializer
from complaints.serializers import ComplaintSerializer
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404

class ClusterListCreate(generics.ListCreateAPIView):
    queryset = Cluster.objects.order_by("-id").all()
    serializer_class = ClusterSerializer

class ClusterDetailAPI(APIView):
    def get(self, request, cluster_id):
        # Получаем кластер по ID
        cluster = get_object_or_404(Cluster, id=cluster_id)

        # Получаем все жалобы, связанные с этим кластером
        complaints = Complaint.objects.filter(cluster=cluster)

        # Сериализуем данные
        cluster_data = ClusterSerializer(cluster).data
        complaints_data = ComplaintSerializer(complaints, many=True).data

        # Возвращаем данные
        return Response({
            **cluster_data,
            'complaints': complaints_data,
        }, status=status.HTTP_200_OK)