from django.shortcuts import render
from rest_framework import generics
from .models import Complaint
from .serializers import ComplaintSerializer

def page(request):
    return render(request, "page.html")

class ComplaintListCreate(generics.ListCreateAPIView):
    queryset = Complaint.objects.all()
    serializer_class = ComplaintSerializer

class ComplaintDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = Complaint.objects.all()
    serializer_class = ComplaintSerializer