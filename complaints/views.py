from django.shortcuts import render
from rest_framework import generics
from clusters.models import Cluster
from .serializers import ComplaintSerializer
from .models import Complaint
import random as rnd
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from .models import Complaint, Cluster

class ComplaintListCreate(generics.ListCreateAPIView):
    queryset = Complaint.objects.all()
    serializer_class = ComplaintSerializer

class ComplaintDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = Complaint.objects.all()
    serializer_class = ComplaintSerializer

def create_complaint(request):
    if request.method == 'POST':
        user_email = request.POST.get('user_email')
        complaint_name = request.POST.get('complaint_name')
        complaint_description = request.POST.get('complaint_text')
        cluster = Cluster.objects.get(id=1)
        new_item = Complaint.objects.create(
            email = user_email,
            name=complaint_name,
            text=complaint_description,
            x=rnd.randint(5, 400),
            y=rnd.randint(5, 400),
            cluster=cluster
        )
        new_item.save()

    return render(request, 'create_complaint.html')

def canvas_view(request):
    complaints = Complaint.objects.all()
    return render(request, 'drawer.html', {'complaints': complaints})

class CreateClusterWithComplaints(APIView):
    def post(self, request):
        # Получаем список ID жалоб из запроса
        complaint_ids = request.data.get('complaint_ids', [])

        # Создаем новый кластер
        new_cluster = Cluster.objects.create(
            name=f"Cluster {Cluster.objects.count() + 1}",  # Автоматическое имя
            summary="Auto-generated cluster"  # Можно изменить или добавить логику для summary
        )

        # Привязываем жалобы к новому кластеру
        for complaint_id in complaint_ids:
            complaint = get_object_or_404(Complaint, id=complaint_id)
            complaint.cluster = new_cluster
            complaint.save()

        return Response(
            {"message": "Cluster created successfully", "cluster_id": new_cluster.id},
            status=status.HTTP_201_CREATED
        )