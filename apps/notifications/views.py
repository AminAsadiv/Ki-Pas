from django.shortcuts import render, get_object_or_404
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views import View
from django.http import JsonResponse
from django.utils import timezone
import datetime
from .models import Notification
from apps.social.models import Friendship
from django.db.models import Q


class NotificationsView(LoginRequiredMixin, View):
    login_url = '/accounts/login/'

    def get(self, request):
        tab = request.GET.get('tab', 'all')
        qs = Notification.objects.filter(recipient=request.user).select_related('actor', 'actor__profile')

        # Tab filtering
        if tab == 'unread':
            notifications = qs.filter(is_read=False)[:60]
        elif tab == 'friends':
            notifications = qs.filter(notification_type__in=['friend_request', 'friend_accepted'])[:40]
        elif tab == 'events':
            notifications = qs.filter(notification_type__in=[
                'event_invitation', 'event_reminder', 'event_update', 'event_cancelled', 'like'
            ])[:40]
        elif tab == 'messages':
            notifications = qs.filter(notification_type='new_message')[:40]
        elif tab == 'system':
            notifications = qs.filter(notification_type__in=[
                'badge_earned', 'level_up', 'xp_earned', 'account_warning', 'report_resolved'
            ])[:40]
        else:
            notifications = qs[:60]

        # Counts for tab badges
        counts = {
            'all': qs.count(),
            'unread': qs.filter(is_read=False).count(),
            'friends': qs.filter(notification_type__in=['friend_request', 'friend_accepted']).count(),
            'events': qs.filter(notification_type__in=['event_invitation', 'event_reminder', 'event_update', 'event_cancelled', 'like']).count(),
            'messages': qs.filter(notification_type='new_message').count(),
            'system': qs.filter(notification_type__in=['badge_earned', 'level_up', 'xp_earned', 'account_warning', 'report_resolved']).count(),
        }

        # Pending friend requests (for inline accept/decline)
        pending_requests = Friendship.objects.filter(
            receiver=request.user, status='pending'
        ).select_related('sender', 'sender__profile')[:10]

        today = timezone.localdate()
        yesterday = today - datetime.timedelta(days=1)

        return render(request, 'notifications/notifications.html', {
            'notifications': notifications,
            'tab': tab,
            'counts': counts,
            'pending_requests': pending_requests,
            'today': today,
            'yesterday': yesterday,
        })


class MarkReadView(LoginRequiredMixin, View):
    login_url = '/accounts/login/'

    def post(self, request, pk):
        Notification.objects.filter(pk=pk, recipient=request.user).update(is_read=True)
        return JsonResponse({'success': True})


class MarkAllReadView(LoginRequiredMixin, View):
    login_url = '/accounts/login/'

    def post(self, request):
        Notification.objects.filter(recipient=request.user, is_read=False).update(is_read=True)
        return JsonResponse({'success': True})


class AcceptFriendView(LoginRequiredMixin, View):
    login_url = '/accounts/login/'

    def post(self, request, pk):
        req = get_object_or_404(Friendship, pk=pk, receiver=request.user, status='pending')
        req.status = 'accepted'
        req.save()
        return JsonResponse({'success': True, 'action': 'accepted'})


class DeclineFriendView(LoginRequiredMixin, View):
    login_url = '/accounts/login/'

    def post(self, request, pk):
        req = get_object_or_404(Friendship, pk=pk, receiver=request.user, status='pending')
        req.delete()
        return JsonResponse({'success': True, 'action': 'declined'})
