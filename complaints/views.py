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
import threading
import uuid
from django.core.cache import cache
import re
from urllib.parse import urlparse

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
        if len(data) > 2:
            new_cluster.model = data[2]
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
            elif cluster.model != 'GigaChat':
                cluster.model = 'OpenRouter'
                cluster.save()
            
            # Регенерируем и сохраняем суммаризацию, используя модель из кластера
            result = cluster.generate_summary(cluster.model)
            
            if isinstance(result, tuple):
                cluster.name = result[0]
                cluster.summary = result[1]
                if len(result) > 2:
                    cluster.model = result[2]
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

# Dictionary to store task status (for simple in-memory task tracking)
tasks_status = {}

def is_valid_youtube_url(url):
    """Validate if the URL is a valid YouTube URL"""
    if not url:
        return False, "YouTube URL is required"
        
    # Check if it's a valid URL
    try:
        parsed_url = urlparse(url)
        if not parsed_url.scheme or not parsed_url.netloc:
            return False, "Invalid URL format. Please enter a complete URL including http:// or https://"
            
        # Check if it's from YouTube - only essential validation
        if not ('youtube.com' in parsed_url.netloc or 'youtu.be' in parsed_url.netloc):
            return False, "The URL must be from YouTube (youtube.com or youtu.be)"
        
        return True, "Valid YouTube URL"
    except Exception as e:
        return False, f"Error validating URL: {str(e)}"

def run_add_youtube_command(task_id, video_url, max_results, batch_size):
    try:
        # Update task status to started
        tasks_status[task_id] = {'status': 'STARTED', 'result': None}
        
        # Validate YouTube URL
        is_valid, message = is_valid_youtube_url(video_url)
        if not is_valid:
            tasks_status[task_id] = {'status': 'FAILURE', 'result': message}
            logger.error(f"Invalid YouTube URL: {message}")
            return
        
        # Run the command
        call_command('add_youtube', video_url, max_results=max_results, batch_size=batch_size)
        
        # Update task status to success
        tasks_status[task_id] = {
            'status': 'SUCCESS', 
            'result': {'success': True, 'success_count': max_results}
        }
    except Exception as e:
        # Update task status to failure
        tasks_status[task_id] = {'status': 'FAILURE', 'result': str(e)}
        logger.error(f"Error in YouTube import task {task_id}: {str(e)}")

@csrf_exempt
def add_youtube_api(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            video_url = data.get('video_url')
            max_results = data.get('max_results', 1000)
            batch_size = data.get('batch_size', 50)
            
            # Validate YouTube URL before starting the thread
            is_valid, message = is_valid_youtube_url(video_url)
            if not is_valid:
                return JsonResponse({"error": message}, status=400)
            
            # Generate a task ID
            task_id = str(uuid.uuid4())
            
            # Start the command in a separate thread
            thread = threading.Thread(
                target=run_add_youtube_command, 
                args=(task_id, video_url, max_results, batch_size)
            )
            thread.daemon = True  # Thread will exit when main program exits
            thread.start()
            
            # Initialize task status
            tasks_status[task_id] = {'status': 'PENDING', 'result': None}
            
            return JsonResponse({"message": "YouTube import started", "task_id": task_id})
        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON format"}, status=400)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)
    else:
        return JsonResponse({"error": "Method not allowed"}, status=405)

@csrf_exempt
def task_status_api(request, task_id):
    """Get the status of a background task"""
    if task_id in tasks_status:
        return JsonResponse(tasks_status[task_id])
    else:
        return JsonResponse({"status": "UNKNOWN", "result": None}, status=404)