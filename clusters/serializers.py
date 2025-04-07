from rest_framework import serializers
from .models import Cluster
from complaints.serializers import ProjectValidatorSerializer

class ClusterSerializer(ProjectValidatorSerializer):
    class Meta:
        model = Cluster
        fields = '__all__'