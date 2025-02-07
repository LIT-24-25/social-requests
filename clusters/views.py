from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views import View
from clusters.models import Cluster
from complaints.models import Complaint
from rest_framework import generics
import json
from .serializers import ClusterSerializer

# class ClusterListView(View):
#     def get(self, request):
#         clusters = Cluster.objects.all().values()
#         return JsonResponse(list(clusters), safe=False)
#
# @method_decorator(csrf_exempt, name='dispatch')
# class ClusterCreateView(View):
#     def post(self, request):
#         data = json.loads(request.body)
#         complaint_ids = data.get('complaint_ids', []) # better to use Serializer here
#         complaints = Complaint.objects.filter(id__in=complaint_ids)
#         cluster = Cluster.objects.create(summary=data.get('summary', ''))
#         cluster.complaints.set(complaints)
#         return JsonResponse({'id': cluster.id, 'summary': cluster.summary})

class ClusterListCreate(generics.ListCreateAPIView):
    queryset = Complaint.objects.all()
    serializer_class = ClusterSerializer

class ClusterDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = Complaint.objects.all()
    serializer_class = ClusterSerializer