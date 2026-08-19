from rest_framework.views import APIView
from rest_framework.response import Response
from apps.accounts.models import User
from apps.events.models import Event


class SearchAPIView(APIView):
    def get(self, request):
        q = request.query_params.get('q', '').strip()
        if not q:
            return Response({'events': [], 'users': []})

        events = Event.objects.filter(
            title__icontains=q, status='published', privacy='public'
        ).select_related('host', 'category').order_by('-created_at')[:10]

        users = User.objects.filter(
            username__icontains=q, is_active=True
        ).select_related('profile').order_by('username')[:10]

        return Response({
            'events': [{'id': e.pk, 'title': e.title, 'location_name': e.location_name,
                        'start_datetime': e.start_datetime.isoformat() if e.start_datetime else None} for e in events],
            'users': [{'username': u.username, 'id': str(u.id),
                       'full_name': getattr(u.profile, 'full_name', '') if hasattr(u, 'profile') else ''} for u in users],
        })
