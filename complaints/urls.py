from django.urls import path
from .views import (
    ComplaintListCreate, ComplaintDetail, CreateClusterWithComplaints, 
    apply_tsne_api, get_cluster_details, regenerate_summary,
    add_youtube_api, task_status_api, search_complaints
)

urlpatterns = [
    path('complaints/', ComplaintListCreate.as_view(), name='complaint-list-create'),
    path('complaints/<int:pk>/', ComplaintDetail.as_view(), name='complaint-detail'),
    path('create-cluster/', CreateClusterWithComplaints.as_view(), name='create-cluster'),
    path('apply_tsne/', apply_tsne_api, name='apply_tsne_api'),
    path('clusters/<int:cluster_id>/details/', get_cluster_details, name='cluster-details'),
    path('regenerate-summary/', regenerate_summary, name='regenerate-summary'),
    
    # New YouTube API endpoints
    path('add-youtube/', add_youtube_api, name='add-youtube-api'),
    path('task-status/<str:task_id>/', task_status_api, name='task-status-api'),
    
    # Search API endpoint
    path('search/', search_complaints, name='search-complaints'),
]