from django.urls import path
from .views import ClusterListCreate, ClusterDetail

urlpatterns = [
    path('clusters/', ClusterListCreate.as_view(), name='cluster-list-create'),
    path('clusters/<int:pk>/', ClusterDetail.as_view(), name='cluster-detail')
]