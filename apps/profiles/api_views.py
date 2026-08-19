from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from django.shortcuts import get_object_or_404
from apps.accounts.models import User


class UserProfileAPIView(APIView):
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get(self, request, username):
        user = get_object_or_404(User, username=username)
        profile = getattr(user, 'profile', None)
        return Response({
            'id': str(user.id),
            'username': user.username,
            'full_name': profile.full_name if profile else '',
            'bio': profile.bio if profile else '',
            'city': profile.city if profile else '',
            'country': profile.country if profile else '',
            'avatar': request.build_absolute_uri(profile.avatar.url) if profile and profile.avatar else None,
            'level': profile.level if profile else 1,
            'xp': profile.xp if profile else 0,
            'level_title': profile.level_title if profile else '',
            'is_verified_host': profile.is_verified_host if profile else False,
            'reputation_score': float(profile.reputation_score) if profile else 0.0,
            'joined': user.date_joined.isoformat(),
        })
