from django.urls import path
from .views import ComplaintListCreate, ComplaintDetail

urlpatterns = [
    path('complaints/', ComplaintListCreate.as_view(), name='complaint-list-create'),
    path('complaints/<int:pk>/', ComplaintDetail.as_view(), name='complaint-detail')
]