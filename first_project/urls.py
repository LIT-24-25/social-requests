"""
URL configuration for first_project project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from complaints.views import create_complaint, canvas_view, CreateClusterWithComplaints
from clusters.views import cluster_list, ClusterDetailAPI

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('complaints.urls')),
    path('', create_complaint),
    path('canvas/', canvas_view),
    path('api/', include('clusters.urls')),
    path('api/create-cluster/', CreateClusterWithComplaints.as_view(), name='create-cluster'),
    path('clusters/', cluster_list, name='cluster-list'),
    path('clusters/<int:cluster_id>/', ClusterDetailAPI.as_view(), name='cluster-detail'),
]
