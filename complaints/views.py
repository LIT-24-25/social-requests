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
from django.core.management import call_command, CommandError
import logging
import threading
import uuid
from projects.models import Project
from sklearn.metrics.pairwise import cosine_similarity
logger = logging.getLogger(__name__)

class ComplaintListCreate(generics.ListCreateAPIView):
    serializer_class = ComplaintSerializer
    
    def get_queryset(self):
        project_id = self.kwargs.get('project_id')
        logger.info(f"ComplaintListCreate.get_queryset called with project_id={project_id}")
        
        if project_id:
            queryset = Complaint.objects.filter(project_id=project_id)
            logger.info(f"Found {queryset.count()} complaints for project_id={project_id}")
            return queryset
        
        queryset = Complaint.objects.all()
        logger.info(f"Found {queryset.count()} complaints (all)")
        return queryset
    
    def get_serializer_context(self):
        context = super().get_serializer_context()
        context.update({'view': self})
        return context

class ComplaintDetail(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = ComplaintSerializer
    
    def get_queryset(self):
        project_id = self.kwargs.get('project_id')
        logger.info(f"ComplaintDetail.get_queryset called with project_id={project_id}")
        
        if project_id:
            queryset = Complaint.objects.filter(project_id=project_id)
            logger.info(f"Found {queryset.count()} complaints for project_id={project_id}")
            return queryset
        
        queryset = Complaint.objects.all()
        logger.info(f"Found {queryset.count()} complaints (all)")
        return queryset
    
    def get_serializer_context(self):
        context = super().get_serializer_context()
        context.update({'view': self})
        return context

@csrf_exempt
def create_complaint(request, project_id=None):
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
            project = None
            if project_id:
                project = get_object_or_404(Project, id=project_id)
                
            new_item = Complaint.objects.create(
                email=user_email,
                name=complaint_name,
                text=complaint_description,
                x=rnd.randint(5, 400),
                y=rnd.randint(5, 400),
                cluster=None,
                project=project
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
            
    return render(request, 'create_complaint.html', {'project_id': project_id})

def visual_view(request, project_id):
    logger.info(f"visual_view called with project_id={project_id}")

    context = {
        'project_id': project_id,
    }
    
    logger.info(f"visual_view: Rendering template without clusters (will be loaded via API)")
    return render(request, 'visual.html', context)

class CreateClusterWithComplaints(APIView):
    def post(self, request, project_id=None):
        logger.info(f"CreateClusterWithComplaints.post called with project_id={project_id}")
        
        complaint_ids = request.data.get('complaint_ids', [])
        model = request.data.get('model')
        
        logger.info(f"Creating cluster with {len(complaint_ids)} complaints, model={model}")
        
        # Получаем проект по ID, если передан
        project = None
        if project_id:
            project = get_object_or_404(Project, id=project_id)
            logger.info(f"Found project with id={project_id}")
        
        # Создаем новый кластер
        new_cluster = Cluster.objects.create(
            name=f"Cluster {Cluster.objects.count() + 1}",
            summary="Генерация описания...",  # Временный текст
            model=model,  # Save the model name
            project=project,  # Добавляем проект в кластер
            size = len(complaint_ids)
        )
        logger.info(f"Created new cluster with id={new_cluster.id}")

        # Привязываем жалобы и обновляем кластер
        for complaint_id in complaint_ids:
            try:
                complaint = get_object_or_404(Complaint, id=complaint_id)
                complaint.cluster = new_cluster
                complaint.save()
                logger.info(f"Added complaint id={complaint_id} to cluster id={new_cluster.id}")
            except Exception as e:
                logger.error(f"Error adding complaint id={complaint_id} to cluster: {str(e)}")
        
        # Генерируем и сохраняем суммаризацию
        try:
            data = new_cluster.generate_summary(model)
            new_cluster.name = data[0]
            new_cluster.summary = data[1]
            if len(data) > 2:
                new_cluster.model = data[2]
            new_cluster.save()
            logger.info(f"Generated summary for cluster id={new_cluster.id}")
        except Exception as e:
            logger.error(f"Error generating summary for cluster id={new_cluster.id}: {str(e)}")

        return Response(
            {"message": "Cluster created successfully", "cluster_id": new_cluster.id},
            status=status.HTTP_201_CREATED
        )

# API для вызова apply_tsne
@csrf_exempt
def apply_tsne_api(request, project_id):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            perplexity = data.get('perplexity')
            if perplexity is None:
                return JsonResponse({"error": "Параметр perplexity отсутствует"}, status=400)

            call_command('applying_T-sne', perplexity=perplexity, project_id=project_id)

            return JsonResponse({"message": f"Функция apply_tsne вызвана успешно для проекта {project_id}"})
        except json.JSONDecodeError:
            return JsonResponse({"error": "Неверный формат JSON"}, status=400)
    else:
        return JsonResponse({"error": "Метод не разрешен"}, status=405)

@csrf_exempt
def clusterise(request, project_id):
    if request.method == 'POST':
        try:

            call_command('clusterising', project_id=project_id, auto_clusters=True)

            return JsonResponse({"message": f"Функция clusterising вызвана успешно для проекта {project_id}"})
        except json.JSONDecodeError:
            return JsonResponse({"error": "Неверный формат JSON"}, status=400)
    else:
        return JsonResponse({"error": "Метод не разрешен"}, status=405)

def get_cluster_details(request, cluster_id, project_id=None):
    try:
        if project_id:
            cluster = get_object_or_404(Cluster, id=cluster_id, project_id=project_id)
        else:
            cluster = get_object_or_404(Cluster, id=cluster_id)
            
        complaints = Complaint.objects.filter(cluster=cluster)
        
        data = {
            'summary': cluster.summary,
            'model': cluster.model,
            'size': cluster.size,
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
def regenerate_summary(request, project_id):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            cluster_id = data.get('cluster_id')
            
            if cluster_id is None:
                return JsonResponse({"error": "Параметр cluster_id отсутствует"}, status=400)
            
            # Получаем кластер, проверяя project_id если указан
            if project_id:
                cluster = get_object_or_404(Cluster, id=cluster_id, project_id=project_id)
            else:
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
                    "model": cluster.model,
                    "size": cluster.size
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

def run_add_youtube_command(task_id, video_url, project_id):
    try:
        # Update task status to started
        tasks_status[task_id] = {'status': 'STARTED', 'result': None}

        # Run the command
        call_command('add_youtube', video_url, project_id)
        
        # Update task status to success
        tasks_status[task_id] = {
            'status': 'SUCCESS', 
            'result': {'success': True}
        }

        call_command('applying_T-sne', perplexity=25, project_id=project_id)

    except Exception as e:
        # Update task status to failure
        tasks_status[task_id] = {'status': 'FAILURE', 'result': str(e)}
        logger.error(f"Error in YouTube import task {task_id}: {str(e)}")

@csrf_exempt
def add_youtube_api(request, project_id):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            video_url = data.get('video_url')
            
            if not video_url:
                return JsonResponse({"error": "video_url is required"}, status=400)
            
            task_id = str(uuid.uuid4())
            
            thread = threading.Thread(
                target=run_add_youtube_command,
                args=(task_id, video_url, project_id)
            )
            thread.start()
            
            # Get initial count
            initial_count = Complaint.objects.filter(project_id=project_id).count()
            
            # Wait for thread to complete
            thread.join()
            
            # Get final count and calculate difference
            final_count = Complaint.objects.filter(project_id=project_id).count()
            imported_count = final_count - initial_count
            
            return JsonResponse({
                "message": f"Successfully imported {imported_count} comments",
                "task_id": task_id
            })
            
        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON format"}, status=400)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)
            
    return JsonResponse({"error": "Method not allowed"}, status=405)

@csrf_exempt
def search_complaints(request, project_id=None):
    """
    API endpoint for searching complaints based on different criteria.
    
    Search types:
    - email: Search by email address (exact or partial match)
    - text: Search in complaint text (contains match)
    - semantic: Search by semantic similarity using embeddings
    """
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            search_type = data.get('search_type', 'text')
            search_query = data.get('search_query', '')
            
            # Check for empty search query
            if not search_query.strip():
                return JsonResponse({'error': 'Search query cannot be empty'}, status=400)
            
            # Get complaints for the project
            if project_id:
                complaints = Complaint.objects.filter(project_id=project_id)
            else:
                complaints = Complaint.objects.all()
            
            results = []
            
            # Perform search based on search type
            if search_type == 'email':
                # Case-insensitive partial match on email
                import re
                escaped_query = re.escape(search_query)
                filtered_complaints = complaints.filter(email__iregex=escaped_query)
                results = list(filtered_complaints.values('id', 'email', 'name', 'text', 'x', 'y', 'cluster'))
                
            elif search_type == 'text':
                # Case-insensitive text search in name or text
                import re
                escaped_query = re.escape(search_query)
                filtered_complaints = complaints.filter(text__iregex=escaped_query)
                results = list(filtered_complaints.values('id', 'email', 'name', 'text', 'x', 'y', 'cluster'))
                
            elif search_type == 'semantic':
                # Semantic search using embeddings
                try:
                    # Generate embedding for the search query
                    query_complaint = Complaint(text=search_query)
                    query_embedding = query_complaint.call_gigachat_embeddings()
                    
                    # Filter complaints with embeddings
                    complaints_with_embeddings = complaints.exclude(embedding=None)
                    
                    # Calculate similarities and get top results
                    similar_complaints = []
                    
                    for complaint in complaints_with_embeddings:
                        if complaint.embedding is not None:
                            # Calculate cosine similarity
                            similarity = cosine_similarity(
                                [query_embedding], 
                                [complaint.embedding]
                            )[0][0]
                            
                            similar_complaints.append({
                                'complaint': complaint,
                                'similarity': similarity
                            })
                    
                    # Sort by similarity (highest first)
                    similar_complaints.sort(key=lambda x: x['similarity'], reverse=True)
                    
                    # Get top results (limit to 5)
                    top_results = similar_complaints[:5]
                    
                    # Create results with similarity score and sorted by similarity
                    results = [
                        {
                            'id': item['complaint'].id,
                            'email': item['complaint'].email,
                            'name': item['complaint'].name,
                            'text': item['complaint'].text,
                            'x': item['complaint'].x,
                            'y': item['complaint'].y,
                            'cluster': item['complaint'].cluster_id,
                            'similarity': round(float(item['similarity']), 3)
                        }
                        for item in top_results
                    ]
                                        
                except Exception as e:
                    logger.error(f"Error during semantic search: {str(e)}")
                    return JsonResponse({'error': f'Semantic search error: {str(e)}'}, status=500)
            else:
                return JsonResponse({'error': 'Invalid search type'}, status=400)
            
            # Return the search results
            return JsonResponse({
                'count': len(results),
                'results': results
            })
            
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON data'}, status=400)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    
    return JsonResponse({'error': 'Only POST method is supported'}, status=405)