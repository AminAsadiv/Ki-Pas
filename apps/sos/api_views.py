from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from django.shortcuts import get_object_or_404
from datetime import timedelta
from .models import SOSRequest


class SOSListAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        lat = request.query_params.get('lat')
        lng = request.query_params.get('lng')
        qs = SOSRequest.objects.filter(status='active').order_by('-created_at')[:50]
        return Response([{
            'id': s.pk, 'message': s.message,
            'latitude': s.latitude, 'longitude': s.longitude,
            'user': s.user.username, 'created_at': s.created_at.isoformat(),
        } for s in qs])


class SOSCreateAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        lat = request.data.get('latitude')
        lng = request.data.get('longitude')
        if not lat or not lng:
            return Response({'detail': 'Location required'}, status=400)
        sos = SOSRequest.objects.create(
            user=request.user,
            latitude=lat, longitude=lng,
            message=request.data.get('message', ''),
            auto_expires_at=timezone.now() + timedelta(hours=2),
        )
        return Response({'id': sos.pk, 'status': sos.status}, status=201)


class SOSResolveAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        sos = get_object_or_404(SOSRequest, pk=pk, user=request.user)
        sos.status = 'resolved'
        sos.resolved_at = timezone.now()
        sos.save()
        return Response({'status': 'resolved'})
