from django.shortcuts import render
from rest_framework import generics
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from clusters.models import Cluster
from .serializers import ComplaintSerializer
from .models import Complaint
from clusters.serializers import ClusterSerializer
import random as rnd

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json

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


# @csrf_exempt
# def selected_complaints(request):
#     if request.method == 'POST':
#         data = json.loads(request.body)
#         selected_ids = data.get('ids', [])
#
#         # Здесь можно выполнить действия с выделенными жалобами
#         print("Выделенные ID:", selected_ids)
#
#         return JsonResponse({'status': 'success'})
#     return JsonResponse({'status': 'error'}, status=400)

class CreateClusterView(APIView):
    def post(self, request):
        cluster_name = request.data.get('name')
        complaint_ids = request.data.get('complaint_ids')

        if not cluster_name or not complaint_ids:
            return Response(
                {'error': 'Missing cluster name or complaint IDs'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Создаем новый кластер
        new_cluster = Cluster.objects.create(name=cluster_name)

        # Обновляем жалобы, добавляя их в новый кластер
        complaints = Complaint.objects.filter(id__in=complaint_ids)
        complaints.update(cluster=new_cluster)

        # Сериализуем результат для ответа
        cluster_serializer = ClusterSerializer(new_cluster)
        complaints_serializer = ComplaintSerializer(complaints, many=True)

        return Response({
            'cluster': cluster_serializer.data,
            'complaints': complaints_serializer.data
        }, status=status.HTTP_201_CREATED)