from django.shortcuts import render
from rest_framework import generics

from clusters.models import Cluster
from .serializers import ComplaintSerializer
from .models import Complaint
import random as rnd

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json

class ComplaintListCreate(generics.ListCreateAPIView):
    queryset = Complaint.objects.all()
    serializer_class = ComplaintSerializer

class ComplaintDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = Complaint.objects.all()
    serializer_class = ComplaintSerializer

def create_complaint(request):
    if request.method == 'POST':
        user_email = request.POST.get('user_email')
        complaint_name = request.POST.get('complaint_name')
        complaint_description = request.POST.get('complaint_text')
        cluster = Cluster.objects.get(id=1)
        new_item = Complaint.objects.create(
            email = user_email,
            name=complaint_name,
            text=complaint_description,
            x=rnd.randint(5, 400),
            y=rnd.randint(5, 400),
            cluster=cluster
        )
        new_item.save()

    return render(request, 'create_complaint.html')

def canvas_view(request):
    complaints = Complaint.objects.all()
    return render(request, 'drawer.html', {'complaints': complaints})


@csrf_exempt
def selected_complaints(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        selected_ids = data.get('ids', [])

        # Здесь можно выполнить действия с выделенными жалобами
        print("Выделенные ID:", selected_ids)

        return JsonResponse({'status': 'success'})
    return JsonResponse({'status': 'error'}, status=400)