from django.shortcuts import render
from rest_framework import generics
from .serializers import ComplaintSerializer
from .models import Complaint

def page(request):
    return render(request, "page.html")

class ComplaintListCreate(generics.ListCreateAPIView):
    queryset = Complaint.objects.all()
    serializer_class = ComplaintSerializer

class ComplaintDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = Complaint.objects.all()
    serializer_class = ComplaintSerializer


def create_complaint(request):
    if request.method == 'POST':
        item_name = request.POST.get('complaint_name')
        item_description = request.POST.get('complaint_text')

        new_item = Complaint.objects.create(name=item_name, text=item_description)
        new_item.save()

    return render(request, 'create_complaint.html')