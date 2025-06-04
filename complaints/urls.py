from django.urls import path
from .views import (
    ComplaintListCreate, ComplaintDetail, CreateClusterWithComplaints, 
    apply_tsne_api, get_cluster_details, regenerate_summary,
    add_youtube_api, search_complaints, clusterise
)

urlpatterns = [
    path('complaints/', ComplaintListCreate.as_view(), name='complaint-list-create'),
    path('complaints/<int:pk>/', ComplaintDetail.as_view(), name='complaint-detail'),
    path('create-cluster/', CreateClusterWithComplaints.as_view(), name='create-cluster'),
    path('apply_tsne/', apply_tsne_api, name='apply_tsne_api'),
    path('clusters/<int:cluster_id>/details/', get_cluster_details, name='cluster-details'),
    path('regenerate-summary/', regenerate_summary, name='regenerate-summary'),
    
    # YouTube API endpoint
    path('add-youtube/', add_youtube_api, name='add-youtube-api'),
    
    # Search API endpoint
    path('search/', search_complaints, name='search-complaints'),
    
    # Clusterising API endpoint
    path('clusterising/', clusterise, name='clusterising'),
]