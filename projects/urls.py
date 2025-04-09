from django.urls import path
from .views import ProjectListCreate#, ProjectDetail

urlpatterns = [
    path('projects/', ProjectListCreate.as_view(), name='cluster-list-create'),
    #path('projects/<int:cluster_id>/', ProjectDetail.as_view(), name='cluster-detail'),
]