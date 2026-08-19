from django.http import JsonResponse
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404
from apps.accounts.models import User
from .models import Friendship, Follow, Block
from django.db.models import Q


class SendFriendRequestView(LoginRequiredMixin, View):
    login_url = '/accounts/login/'

    def post(self, request, username):
        receiver = get_object_or_404(User, username=username)
        if receiver == request.user:
            return JsonResponse({'error': 'Cannot friend yourself'}, status=400)
        if Block.objects.filter(Q(blocker=request.user, blocked=receiver) | Q(blocker=receiver, blocked=request.user)).exists():
            return JsonResponse({'error': 'Blocked'}, status=400)
        obj, created = Friendship.objects.get_or_create(sender=request.user, receiver=receiver)
        return JsonResponse({'status': obj.status, 'created': created})


class AcceptFriendRequestView(LoginRequiredMixin, View):
    login_url = '/accounts/login/'

    def post(self, request, pk):
        friendship = get_object_or_404(Friendship, pk=pk, receiver=request.user, status='pending')
        friendship.status = 'accepted'
        friendship.save()
        return JsonResponse({'status': 'accepted'})


class DeclineFriendRequestView(LoginRequiredMixin, View):
    login_url = '/accounts/login/'

    def post(self, request, pk):
        friendship = get_object_or_404(Friendship, pk=pk, receiver=request.user)
        friendship.delete()
        return JsonResponse({'status': 'declined'})


class FollowView(LoginRequiredMixin, View):
    login_url = '/accounts/login/'

    def post(self, request, username):
        user = get_object_or_404(User, username=username)
        if user == request.user:
            return JsonResponse({'error': 'Cannot follow yourself'}, status=400)
        follow, created = Follow.objects.get_or_create(follower=request.user, following=user)
        if not created:
            follow.delete()
            return JsonResponse({'following': False})
        return JsonResponse({'following': True})


class BlockView(LoginRequiredMixin, View):
    login_url = '/accounts/login/'

    def post(self, request, username):
        user = get_object_or_404(User, username=username)
        block, created = Block.objects.get_or_create(blocker=request.user, blocked=user)
        Friendship.objects.filter(
            Q(sender=request.user, receiver=user) | Q(sender=user, receiver=request.user)
        ).delete()
        return JsonResponse({'blocked': True})

    def delete(self, request, username):
        user = get_object_or_404(User, username=username)
        Block.objects.filter(blocker=request.user, blocked=user).delete()
        return JsonResponse({'blocked': False})
