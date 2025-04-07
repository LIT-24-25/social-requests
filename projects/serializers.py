from .models import Project
from complaints.serializers import ProjectValidatorSerializer

class ProjectSerializer(ProjectValidatorSerializer):
    class Meta:
        model = Project
        fields = '__all__'