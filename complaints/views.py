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
from clusters.views import ClusterListCreate
import logging

logger = logging.getLogger(__name__)

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
            
            # Генерируем эмбеддинги для жалобы
            try:
                new_item.call_gigachat_embeddings()
                new_item.save()
            except Exception as e:
                logger.error(f"Error generating embeddings for complaint {new_item.id}: {str(e)}")
            
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

def visual_view(request):
    # Get clusters using ClusterListCreate API
    cluster_view = ClusterListCreate()
    cluster_view.request = request
    clusters = cluster_view.get_queryset()
    
    clusters_data = json.dumps([{
        'id': cluster.id,
        'name': cluster.name,
        'summary': cluster.summary
    } for cluster in clusters])
    
    context = {
        'total_clusters': clusters.count(),
        'clusters': clusters_data,
    }
    return render(request, 'visual.html', context)

class CreateClusterWithComplaints(APIView):
    def post(self, request):
        complaint_ids = request.data.get('complaint_ids', [])
        model = request.data.get('model')
        
        # Создаем новый кластер
        new_cluster = Cluster.objects.create(
            name=f"Cluster {Cluster.objects.count() + 1}",
            summary="Генерация описания...",  # Временный текст
            model=model  # Save the model name
        )

        # Привязываем жалобы и обновляем кластер
        for complaint_id in complaint_ids:
            complaint = get_object_or_404(Complaint, id=complaint_id)
            complaint.cluster = new_cluster
            complaint.save()
        
        # Генерируем и сохраняем суммаризацию
        data  = new_cluster.generate_summary(model)
        new_cluster.name = data[0]
        new_cluster.summary = data[1]
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
            'model': cluster.model,
            'complaints': [{
                'id': complaint.id,
                'name': complaint.name,
                'text': complaint.text
            } for complaint in complaints]
        }
        
        return JsonResponse(data)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@csrf_exempt
def regenerate_summary(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            cluster_id = data.get('cluster_id')
            
            if cluster_id is None:
                return JsonResponse({"error": "Параметр cluster_id отсутствует"}, status=400)
            
            # Получаем кластер
            cluster = get_object_or_404(Cluster, id=cluster_id)
            
            # Ensure model is set, default to GigaChat if not
            if not cluster.model:
                cluster.model = 'GigaChat'
                cluster.save()
            
            # Регенерируем и сохраняем суммаризацию, используя модель из кластера
            result = cluster.generate_summary(cluster.model)
            
            if isinstance(result, tuple) and len(result) == 2:
                cluster.name = result[0]
                cluster.summary = result[1]
                cluster.save()
                
                return JsonResponse({
                    "message": "Суммаризация кластера успешно обновлена",
                    "name": cluster.name,
                    "summary": cluster.summary,
                    "model": cluster.model
                })
            else:
                return JsonResponse({"error": "Некорректный результат генерации"}, status=500)
                
        except json.JSONDecodeError:
            return JsonResponse({"error": "Неверный формат JSON"}, status=400)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)
    else:
        return JsonResponse({"error": "Метод не разрешен"}, status=405)