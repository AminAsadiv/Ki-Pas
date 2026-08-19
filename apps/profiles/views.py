from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views import View
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Q
from apps.accounts.models import User
from apps.social.models import Friendship, Follow, Block


class MyProfileView(LoginRequiredMixin, View):
    login_url = '/accounts/login/'

    def get(self, request):
        return redirect('profiles:public_profile', username=request.user.username)


class PublicProfileView(View):
    def get(self, request, username):
        profile_user = get_object_or_404(User, username=username)
        profile = get_object_or_404(User, username=username)
        try:
            user_profile = profile_user.profile
        except Exception:
            from apps.profiles.models import Profile
            user_profile, _ = Profile.objects.get_or_create(user=profile_user)

        is_own = request.user.is_authenticated and request.user == profile_user
        is_friend = False
        is_following = False
        friendship_status = None
        is_blocked = False

        if request.user.is_authenticated and not is_own:
            try:
                friendship = Friendship.objects.get(
                    Q(sender=request.user, receiver=profile_user) |
                    Q(sender=profile_user, receiver=request.user)
                )
                friendship_status = friendship.status
                is_friend = friendship.status == 'accepted'
            except Exception:
                pass
            is_following = Follow.objects.filter(follower=request.user, following=profile_user).exists()
            is_blocked = Block.objects.filter(blocker=request.user, blocked=profile_user).exists()

        from apps.events.models import Event
        hosted_events = Event.objects.filter(host=profile_user, status='published').order_by('-created_at').select_related('host', 'host__profile', 'category')[:12]
        from apps.gamification.models import UserBadge
        badges = UserBadge.objects.filter(user=profile_user).select_related('badge')[:12]
        from apps.reviews.models import HostReview
        from django.db.models import Avg
        reviews_qs = HostReview.objects.filter(host=profile_user).select_related('reviewer', 'reviewer__profile', 'event')
        reviews = reviews_qs[:10]
        avg_rating_data = reviews_qs.aggregate(avg=Avg('rating'))
        avg_rating = round(avg_rating_data['avg'], 1) if avg_rating_data['avg'] else None

        friends = []
        try:
            accepted = Friendship.objects.filter(
                Q(sender=profile_user, status='accepted') | Q(receiver=profile_user, status='accepted')
            ).select_related('sender', 'sender__profile', 'receiver', 'receiver__profile')[:16]
            for f in accepted:
                friend = f.receiver if f.sender == profile_user else f.sender
                friends.append(friend)
        except Exception:
            pass

        followers_count = Follow.objects.filter(following=profile_user).count()
        following_count = Follow.objects.filter(follower=profile_user).count()

        # Annotate user join/like/save status on hosted events
        if request.user.is_authenticated:
            from apps.events.models import EventParticipant, EventLike, EventSave
            joined_ids = set(EventParticipant.objects.filter(user=request.user, status='approved').values_list('event_id', flat=True))
            liked_ids = set(EventLike.objects.filter(user=request.user).values_list('event_id', flat=True))
            saved_ids = set(EventSave.objects.filter(user=request.user).values_list('event_id', flat=True))
            for e in hosted_events:
                e.user_joined = e.id in joined_ids
                e.user_liked = e.id in liked_ids
                e.user_saved = e.id in saved_ids

        context = {
            'profile_user': profile_user,
            'user_profile': user_profile,
            'is_own': is_own,
            'is_friend': is_friend,
            'is_following': is_following,
            'friendship_status': friendship_status,
            'is_blocked': is_blocked,
            'hosted_events': hosted_events,
            'badges': badges,
            'reviews': reviews,
            'avg_rating': avg_rating,
            'friends': friends,
            'followers_count': followers_count,
            'following_count': following_count,
        }
        return render(request, 'profiles/profile.html', context)


class ProfileSettingsView(LoginRequiredMixin, View):
    login_url = '/accounts/login/'

    def get(self, request):
        try:
            user_profile = request.user.profile
        except Exception:
            from apps.profiles.models import Profile
            user_profile, _ = Profile.objects.get_or_create(user=request.user)
        from apps.notifications.models import NotificationPreference
        notif_pref, _ = NotificationPreference.objects.get_or_create(user=request.user)
        section = request.GET.get('section', 'profile')
        return render(request, 'profiles/settings.html', {
            'user_profile': user_profile,
            'notif_pref': notif_pref,
            'section': section,
            'saved': request.GET.get('saved', ''),
        })

    def post(self, request):
        try:
            user_profile = request.user.profile
        except Exception:
            from apps.profiles.models import Profile
            user_profile, _ = Profile.objects.get_or_create(user=request.user)

        section = request.POST.get('section', 'profile')

        if section == 'profile':
            user_profile.full_name = request.POST.get('full_name', '').strip()
            user_profile.bio = request.POST.get('bio', '').strip()
            user_profile.city = request.POST.get('city', '').strip()
            user_profile.country = request.POST.get('country', '').strip()
            user_profile.website = request.POST.get('website', '').strip()
            user_profile.instagram = request.POST.get('instagram', '').strip()
            user_profile.twitter = request.POST.get('twitter', '').strip()
            user_profile.linkedin = request.POST.get('linkedin', '').strip()
            user_profile.date_of_birth = request.POST.get('date_of_birth') or None
            if 'avatar' in request.FILES:
                user_profile.avatar = request.FILES['avatar']
            if 'cover_photo' in request.FILES:
                user_profile.cover_photo = request.FILES['cover_photo']
            user_profile.save()

        elif section == 'account':
            new_username = request.POST.get('username', '').strip()
            if new_username and new_username != request.user.username:
                from apps.accounts.models import User as AppUser
                if not AppUser.objects.filter(username=new_username).exclude(pk=request.user.pk).exists():
                    request.user.username = new_username
                    request.user.save(update_fields=['username'])

        elif section == 'security':
            old_pw = request.POST.get('old_password', '')
            new_pw = request.POST.get('new_password', '')
            if old_pw and new_pw and request.user.check_password(old_pw):
                request.user.set_password(new_pw)
                request.user.save()
                from django.contrib.auth import update_session_auth_hash
                update_session_auth_hash(request, request.user)

        elif section == 'privacy':
            user_profile.is_public = request.POST.get('is_public') == 'on'
            user_profile.show_email = request.POST.get('show_email') == 'on'
            user_profile.show_friends = request.POST.get('show_friends') == 'on'
            user_profile.who_can_message = request.POST.get('who_can_message', user_profile.who_can_message)
            user_profile.who_can_friend = request.POST.get('who_can_friend', user_profile.who_can_friend)
            user_profile.share_location = request.POST.get('share_location') == 'on'
            user_profile.save()

        elif section == 'notifications':
            from apps.notifications.models import NotificationPreference
            pref, _ = NotificationPreference.objects.get_or_create(user=request.user)
            pref.email_friend_requests = request.POST.get('email_friend_requests') == 'on'
            pref.email_event_reminders = request.POST.get('email_event_reminders') == 'on'
            pref.email_event_updates = request.POST.get('email_event_updates') == 'on'
            pref.email_new_messages = request.POST.get('email_new_messages') == 'on'
            pref.email_weekly_digest = request.POST.get('email_weekly_digest') == 'on'
            pref.push_friend_requests = request.POST.get('push_friend_requests') == 'on'
            pref.push_event_reminders = request.POST.get('push_event_reminders') == 'on'
            pref.push_new_messages = request.POST.get('push_new_messages') == 'on'
            pref.push_likes = request.POST.get('push_likes') == 'on'
            pref.save()

        elif section == 'appearance':
            user_profile.dark_mode = request.POST.get('dark_mode') == 'on'
            user_profile.language = request.POST.get('language', user_profile.language)
            user_profile.save()

        elif section == 'danger':
            action = request.POST.get('danger_action', '')
            if action == 'deactivate':
                request.user.is_deactivated = True
                request.user.save(update_fields=['is_deactivated'])
                from django.contrib.auth import logout
                logout(request)
                return redirect('/')

        return redirect(f'/profile/settings/?section={section}&saved=1')
