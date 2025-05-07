from django.urls import path
from .views import ProjectListCreate, projects_list_view

urlpatterns = [
    path('api/projects/', ProjectListCreate.as_view(), name='project-list-create'),
    path('', projects_list_view, name='projects-list')
]