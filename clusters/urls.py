from django.urls import path
from .views import ClusterListCreate, ClusterDetailAPI

urlpatterns = [
    path('clusters/', ClusterListCreate.as_view(), name='cluster-list-create'),
    path('clusters/<int:cluster_id>/', ClusterDetailAPI.as_view(), name='cluster-detail'),
]