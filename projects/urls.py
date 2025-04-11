from django.urls import path
from .views import ProjectListCreate, projects_list_view

urlpatterns = [
    path('api/projects/', ProjectListCreate.as_view(), name='project-list-create'),
    path('projects/', projects_list_view, name='projects-list'),
    #path('projects/<int:cluster_id>/', ProjectDetail.as_view(), name='cluster-detail'),
]