from rest_framework import serializers
from .models import Complaint
from rest_framework.exceptions import ValidationError

class ProjectValidatorSerializer(serializers.ModelSerializer):
    """
    Базовый сериализатор с валидацией project_id.
    """
    def validate(self, data):
        """
        Проверяет, что project_id из URL совпадает с project_id модели.
        """
        view = self.context.get('view')
        request = self.context.get('request')
        
        if request and view:
            url_project_id = view.kwargs.get('project_id')
            if url_project_id is not None and data.get('project') is not None:
                model_project_id = data['project'].id
                if int(url_project_id) != model_project_id:
                    raise ValidationError(
                        {"project": f"Project ID в URL ({url_project_id}) не совпадает с ID в данных ({model_project_id})"}
                    )
        
        return data

class ComplaintSerializer(ProjectValidatorSerializer):
    class Meta:
        model = Complaint
        fields = '__all__'