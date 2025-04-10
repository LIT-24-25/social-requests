from rest_framework import generics
from .serializers import ProjectSerializer
from .models import Project

class ProjectListCreate(generics.ListCreateAPIView):
    serializer_class = ProjectSerializer

    def get_queryset(self):
        project_id = self.kwargs.get('project_id')

        if project_id:
            queryset = Project.objects.filter(project_id=project_id)
            return queryset

        queryset = Project.objects.all()
        return queryset

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context.update({'view': self})
        return context


