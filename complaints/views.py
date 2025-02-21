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
from django.http import JsonResponse
import json
from django.views.decorators.csrf import csrf_exempt

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
        cluster = None
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

def apply_tsne(step):
    print(f"Функция apply_tsne вызвана с step = {step}")
    # Здесь можно добавить логику, если нужно
    pass

# API для вызова apply_tsne
@csrf_exempt
def apply_tsne_api(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            step = data.get('step')
            if step is None:
                return JsonResponse({"error": "Параметр step отсутствует"}, status=400)
            # Вызываем функцию apply_tsne
            apply_tsne(step)

            return JsonResponse({"message": "Функция apply_tsne вызвана успешно"})
        except json.JSONDecodeError:
            return JsonResponse({"error": "Неверный формат JSON"}, status=400)
    else:
        return JsonResponse({"error": "Метод не разрешен"}, status=405)