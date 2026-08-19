from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly, AllowAny
from rest_framework import status
from django.utils import timezone
from .models import Event, EventCategory, EventParticipant, EventLike, EventSave


def event_to_dict(event, request=None):
    cover = None
    if event.cover_image:
        cover = request.build_absolute_uri(event.cover_image.url) if request else event.cover_image.url
    return {
        'id': event.pk,
        'title': event.title,
        'description': event.description,
        'cover_image': cover,
        'start_datetime': event.start_datetime.isoformat() if event.start_datetime else None,
        'end_datetime': event.end_datetime.isoformat() if event.end_datetime else None,
        'location_name': event.location_name,
        'latitude': float(event.latitude) if event.latitude else None,
        'longitude': float(event.longitude) if event.longitude else None,
        'category': {'id': event.category.pk, 'name': event.category.name, 'slug': event.category.slug} if event.category else None,
        'privacy': event.privacy,
        'event_type': event.event_type,
        'status': event.status,
        'capacity': event.capacity,
        'participant_count': event.participant_count,
        'is_full': event.is_full,
        'host': {'username': event.host.username, 'id': str(event.host.id)},
        'created_at': event.created_at.isoformat(),
    }


class EventListCreateAPIView(APIView):
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get(self, request):
        qs = Event.objects.filter(status='published', privacy='public').select_related('host', 'category').order_by('-created_at')
        category = request.query_params.get('category')
        if category:
            qs = qs.filter(category__slug=category)
        q = request.query_params.get('q')
        if q:
            qs = qs.filter(title__icontains=q)
        limit = min(int(request.query_params.get('limit', 20)), 100)
        offset = int(request.query_params.get('offset', 0))
        total = qs.count()
        events = qs[offset:offset+limit]
        return Response({'count': total, 'results': [event_to_dict(e, request) for e in events]})

    def post(self, request):
        data = request.data
        category_id = data.get('category')
        cat = None
        if category_id:
            try:
                cat = EventCategory.objects.get(pk=category_id)
            except EventCategory.DoesNotExist:
                return Response({'category': 'Invalid category'}, status=400)
        event = Event.objects.create(
            host=request.user,
            title=data.get('title', ''),
            description=data.get('description', ''),
            category=cat,
            privacy=data.get('privacy', 'public'),
            event_type=data.get('event_type', 'free'),
            status=data.get('status', 'draft'),
            location_name=data.get('location_name', ''),
            latitude=data.get('latitude'),
            longitude=data.get('longitude'),
        )
        return Response(event_to_dict(event, request), status=201)


class EventDetailAPIView(APIView):
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get(self, request, pk):
        try:
            event = Event.objects.select_related('host', 'category').get(pk=pk)
        except Event.DoesNotExist:
            return Response({'detail': 'Not found'}, status=404)
        data = event_to_dict(event, request)
        if request.user.is_authenticated:
            data['is_liked'] = EventLike.objects.filter(event=event, user=request.user).exists()
            data['is_saved'] = EventSave.objects.filter(event=event, user=request.user).exists()
            data['participant_status'] = None
            p = EventParticipant.objects.filter(event=event, user=request.user).first()
            if p:
                data['participant_status'] = p.status
        return Response(data)

    def patch(self, request, pk):
        try:
            event = Event.objects.get(pk=pk, host=request.user)
        except Event.DoesNotExist:
            return Response({'detail': 'Not found or not authorized'}, status=404)
        for field in ('title', 'description', 'privacy', 'status', 'location_name', 'latitude', 'longitude'):
            if field in request.data:
                setattr(event, field, request.data[field])
        event.save()
        return Response(event_to_dict(event, request))

    def delete(self, request, pk):
        try:
            event = Event.objects.get(pk=pk, host=request.user)
        except Event.DoesNotExist:
            return Response({'detail': 'Not found'}, status=404)
        event.delete()
        return Response(status=204)


class EventJoinAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        try:
            event = Event.objects.get(pk=pk)
        except Event.DoesNotExist:
            return Response({'detail': 'Not found'}, status=404)
        if event.host == request.user:
            return Response({'detail': 'Host cannot join own event'}, status=400)
        if event.is_full and not event.allow_waitlist:
            return Response({'detail': 'Event is full'}, status=400)
        p_status = 'waitlist' if event.is_full else ('pending' if event.requires_approval else 'approved')
        obj, created = EventParticipant.objects.get_or_create(event=event, user=request.user, defaults={'status': p_status})
        if not created:
            return Response({'detail': 'Already joined', 'status': obj.status})
        return Response({'status': obj.status}, status=201)


class EventLeaveAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        deleted, _ = EventParticipant.objects.filter(event_id=pk, user=request.user).delete()
        if deleted:
            return Response({'detail': 'Left event'})
        return Response({'detail': 'Not a participant'}, status=400)


class EventLikeAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        try:
            event = Event.objects.get(pk=pk)
        except Event.DoesNotExist:
            return Response({'detail': 'Not found'}, status=404)
        like, created = EventLike.objects.get_or_create(event=event, user=request.user)
        if not created:
            like.delete()
            return Response({'liked': False})
        return Response({'liked': True})


class EventSaveAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        try:
            event = Event.objects.get(pk=pk)
        except Event.DoesNotExist:
            return Response({'detail': 'Not found'}, status=404)
        save, created = EventSave.objects.get_or_create(event=event, user=request.user)
        if not created:
            save.delete()
            return Response({'saved': False})
        return Response({'saved': True})


class CategoryListAPIView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        cats = EventCategory.objects.all().order_by('order')
        return Response([{'id': c.pk, 'name': c.name, 'slug': c.slug, 'icon': c.icon} for c in cats])


class FeedAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        from apps.social.models import Follow
        following_ids = Follow.objects.filter(follower=request.user).values_list('following_id', flat=True)
        qs = Event.objects.filter(
            host_id__in=following_ids, status='published'
        ).select_related('host', 'category').order_by('-created_at')[:20]
        return Response([event_to_dict(e, request) for e in qs])
