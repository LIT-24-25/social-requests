from django.shortcuts import render
from rest_framework import generics
from .models import Project
from .serializers import ProjectSerializer

class ProjectListCreate(generics.ListCreateAPIView):
    queryset = Project.objects.all()
    serializer_class = ProjectSerializer

def projects_list_view(request):
    # Simply render the template, frontend will fetch data from API
    return render(request, 'projects_list.html')
