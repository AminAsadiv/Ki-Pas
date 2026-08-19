from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from apps.accounts.models import User
from .models import Follow, Friendship, Block


class FollowAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, username):
        target = get_object_or_404(User, username=username)
        if target == request.user:
            return Response({'detail': 'Cannot follow yourself'}, status=400)
        follow, created = Follow.objects.get_or_create(follower=request.user, following=target)
        if not created:
            follow.delete()
            return Response({'following': False})
        return Response({'following': True})


class FriendRequestAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, username):
        target = get_object_or_404(User, username=username)
        if target == request.user:
            return Response({'detail': 'Cannot add yourself'}, status=400)
        from django.db.models import Q
        existing = Friendship.objects.filter(
            Q(sender=request.user, receiver=target) | Q(sender=target, receiver=request.user)
        ).first()
        if existing:
            return Response({'detail': 'Request already exists', 'status': existing.status})
        req = Friendship.objects.create(sender=request.user, receiver=target, status='pending')
        return Response({'id': req.pk, 'status': req.status}, status=201)


class AcceptFriendAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        req = get_object_or_404(Friendship, pk=pk, receiver=request.user, status='pending')
        req.status = 'accepted'
        req.save()
        return Response({'status': 'accepted'})


class DeclineFriendAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        req = get_object_or_404(Friendship, pk=pk, receiver=request.user, status='pending')
        req.delete()
        return Response({'status': 'declined'})


class BlockAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, username):
        target = get_object_or_404(User, username=username)
        block, created = Block.objects.get_or_create(blocker=request.user, blocked=target)
        if not created:
            block.delete()
            return Response({'blocked': False})
        return Response({'blocked': True})


class FriendsListAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        from django.db.models import Q
        friendships = Friendship.objects.filter(
            Q(sender=request.user) | Q(receiver=request.user), status='accepted'
        ).select_related('sender__profile', 'receiver__profile')
        friends = []
        for f in friendships:
            friend = f.receiver if f.sender == request.user else f.sender
            friends.append({'username': friend.username, 'id': str(friend.id),
                           'full_name': getattr(friend.profile, 'full_name', '') if hasattr(friend, 'profile') else ''})
        return Response(friends)
