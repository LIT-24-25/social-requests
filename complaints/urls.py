from django.urls import path
from .views import ComplaintListCreate, ComplaintDetail, CreateClusterWithComplaints, apply_tsne_api, get_cluster_details, regenerate_summary

urlpatterns = [
    path('complaints/', ComplaintListCreate.as_view(), name='complaint-list-create'),
    path('complaints/<int:pk>/', ComplaintDetail.as_view(), name='complaint-detail'),
    path('create-cluster/', CreateClusterWithComplaints.as_view(), name='create-cluster'),
    path('apply-tsne/', apply_tsne_api, name='apply_tsne_api'),
    path('api/clusters/<int:cluster_id>/details/', get_cluster_details, name='cluster-details'),
    path('clusters/<int:cluster_id>/details/', get_cluster_details, name='cluster-details'),
    path('regenerate-summary/', regenerate_summary, name='regenerate-summary'),
]