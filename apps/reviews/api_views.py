from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly
from django.shortcuts import get_object_or_404
from apps.accounts.models import User
from apps.events.models import Event
from .models import HostReview, EventReview


def review_dict(r):
    return {
        'id': r.pk, 'rating': r.rating, 'comment': r.comment,
        'reviewer': r.reviewer.username, 'created_at': r.created_at.isoformat(),
    }


class HostReviewListAPIView(APIView):
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get(self, request, username):
        host = get_object_or_404(User, username=username)
        reviews = HostReview.objects.filter(host=host).select_related('reviewer').order_by('-created_at')
        return Response([review_dict(r) for r in reviews])


class CreateHostReviewAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, username):
        host = get_object_or_404(User, username=username)
        if host == request.user:
            return Response({'detail': 'Cannot review yourself'}, status=400)
        rating = int(request.data.get('rating', 0))
        if not 1 <= rating <= 5:
            return Response({'rating': 'Must be 1-5'}, status=400)
        r, created = HostReview.objects.get_or_create(
            host=host, reviewer=request.user,
            defaults={'rating': rating, 'comment': request.data.get('comment', '')}
        )
        if not created:
            r.rating = rating
            r.comment = request.data.get('comment', r.comment)
            r.save()
        return Response(review_dict(r), status=201 if created else 200)


class EventReviewListAPIView(APIView):
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get(self, request, event_id):
        event = get_object_or_404(Event, pk=event_id)
        reviews = EventReview.objects.filter(event=event).select_related('reviewer').order_by('-created_at')
        return Response([review_dict(r) for r in reviews])


class CreateEventReviewAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, event_id):
        event = get_object_or_404(Event, pk=event_id)
        rating = int(request.data.get('rating', 0))
        if not 1 <= rating <= 5:
            return Response({'rating': 'Must be 1-5'}, status=400)
        r, created = EventReview.objects.get_or_create(
            event=event, reviewer=request.user,
            defaults={'rating': rating, 'comment': request.data.get('comment', '')}
        )
        if not created:
            r.rating = rating
            r.comment = request.data.get('comment', r.comment)
            r.save()
        return Response(review_dict(r), status=201 if created else 200)
