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
from django.core.management import call_command
from django.http import HttpResponse
from django.core.serializers import serialize


class ComplaintListCreate(generics.ListCreateAPIView):
    queryset = Complaint.objects.all()
    serializer_class = ComplaintSerializer

class ComplaintDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = Complaint.objects.all()
    serializer_class = ComplaintSerializer

@csrf_exempt
def create_complaint(request):
    if request.method == 'POST':
        try:
            # Парсим JSON данные из тела запроса
            data = json.loads(request.body)
            
            # Получаем данные из JSON
            user_email = data.get('email')
            complaint_name = data.get('name')
            complaint_description = data.get('text')
            
            # Проверяем наличие всех необходимых данных
            if not all([user_email, complaint_name, complaint_description]):
                return JsonResponse({
                    'success': False,
                    'message': 'Все поля должны быть заполнены'
                }, status=400)

            # Создаем новую жалобу
            new_item = Complaint.objects.create(
                email=user_email,
                name=complaint_name,
                text=complaint_description,
                x=rnd.randint(5, 400),
                y=rnd.randint(5, 400),
                cluster=None
            )
            
            return JsonResponse({
                'success': True,
                'message': 'Жалоба успешно создана'
            })
            
        except json.JSONDecodeError:
            return JsonResponse({
                'success': False,
                'message': 'Неверный формат данных'
            }, status=400)
            
    return render(request, 'create_complaint.html')

def canvas_view(request):
    clusters = Cluster.objects.all()
    clusters_data = json.dumps([{
        'id': cluster.id,
        'name': cluster.name
    } for cluster in clusters])
    
    context = {
        'total_clusters': clusters.count(),
        'clusters': clusters_data,
    }
    return render(request, 'drawer.html', context)

class CreateClusterWithComplaints(APIView):
    def post(self, request):
        complaint_ids = request.data.get('complaint_ids', [])
        model = request.data.get('model')
        
        # Создаем новый кластер
        new_cluster = Cluster.objects.create(
            name=f"Cluster {Cluster.objects.count() + 1}",
            summary="Генерация описания..."  # Временный текст
        )

        # Привязываем жалобы и обновляем кластер
        for complaint_id in complaint_ids:
            complaint = get_object_or_404(Complaint, id=complaint_id)
            complaint.cluster = new_cluster
            complaint.save()
        
        # Генерируем и сохраняем суммаризацию
        new_cluster.summary = new_cluster.generate_summary(model)
        new_cluster.save()

        return Response(
            {"message": "Cluster created successfully", "cluster_id": new_cluster.id},
            status=status.HTTP_201_CREATED
        )

def apply_tsne(perplexity):
    call_command('applying_T-sne', perplexity=perplexity)
    return HttpResponse('')

# API для вызова apply_tsne
@csrf_exempt
def apply_tsne_api(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            perplexity = data.get('perplexity')
            if perplexity is None:
                return JsonResponse({"error": "Параметр perplexity отсутствует"}, status=400)
            # Вызываем функцию apply_tsne
            apply_tsne(perplexity)

            return JsonResponse({"message": "Функция apply_tsne вызвана успешно"})
        except json.JSONDecodeError:
            return JsonResponse({"error": "Неверный формат JSON"}, status=400)
    else:
        return JsonResponse({"error": "Метод не разрешен"}, status=405)

def get_cluster_details(request, cluster_id):
    try:
        cluster = get_object_or_404(Cluster, id=cluster_id)
        complaints = Complaint.objects.filter(cluster=cluster)
        
        data = {
            'summary': cluster.summary,
            'complaints': [{
                'id': complaint.id,
                'name': complaint.name,
                'text': complaint.text
            } for complaint in complaints]
        }
        
        return JsonResponse(data)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)