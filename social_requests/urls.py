from django.contrib import admin
from django.urls import path, include
from complaints.views import create_complaint, visual_view

urlpatterns = [
    path('admin/', admin.site.urls),
    path('project/<int:project_id>/api/', include('complaints.urls')),
    path('project/<int:project_id>/api/', include('clusters.urls')),
    path('', include('projects.urls')),
    #path('project/<int:project_id>/api/', include('projects.urls')),

    path('project/<int:project_id>/', create_complaint),
    path('project/<int:project_id>/visual/', visual_view),
]
