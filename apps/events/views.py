from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views import View
from django.http import JsonResponse
from django.utils import timezone
from django.db.models import Q, Count
from .models import Event, EventCategory, EventParticipant, EventLike, EventSave, EventGallery


class LandingView(View):
    def get(self, request):
        if request.user.is_authenticated:
            return redirect('events:feed')
        featured_events = Event.objects.filter(status='published').select_related('host', 'category').order_by('-view_count')[:6]
        categories = EventCategory.objects.annotate(event_count=Count('events')).order_by('order')[:12]
        stats = {
            'total_events': Event.objects.filter(status='published').count(),
            'total_users': 0,
            'total_cities': Event.objects.filter(status='published').values('location_name').distinct().count(),
            'total_categories': EventCategory.objects.count(),
        }
        try:
            from apps.accounts.models import User
            stats['total_users'] = User.objects.filter(is_active=True).count()
        except Exception:
            pass
        return render(request, 'landing.html', {'featured_events': featured_events, 'categories': categories, 'stats': stats})


class FeedView(LoginRequiredMixin, View):
    login_url = '/accounts/login/'

    def get(self, request):
        tab = request.GET.get('tab', 'foryou')
        category_slug = request.GET.get('category', '')
        qs = Event.objects.filter(status='published').select_related('host', 'host__profile', 'category')

        if category_slug:
            qs = qs.filter(category__slug=category_slug)

        if tab == 'nearby':
            try:
                profile = request.user.profile
                if profile.latitude and profile.longitude:
                    qs = qs.filter(latitude__isnull=False, longitude__isnull=False)
                else:
                    qs = qs.none()
            except Exception:
                qs = qs.none()
        elif tab == 'friends':
            from apps.social.models import Friendship
            friend_ids = Friendship.objects.filter(
                Q(sender=request.user, status='accepted') | Q(receiver=request.user, status='accepted')
            ).values_list('sender_id', 'receiver_id')
            flat_ids = set()
            for s, r in friend_ids:
                flat_ids.add(str(s)); flat_ids.add(str(r))
            flat_ids.discard(str(request.user.id))
            qs = qs.filter(host_id__in=flat_ids)
        elif tab == 'saved':
            saved_event_ids = EventSave.objects.filter(user=request.user).values_list('event_id', flat=True)
            qs = qs.filter(id__in=saved_event_ids)
        elif tab == 'trending':
            qs = qs.order_by('-like_count', '-view_count')
        else:
            qs = qs.order_by('-created_at')

        if tab not in ('trending',) and not category_slug:
            qs = qs.order_by('-created_at')

        events = list(qs[:30])
        joined_ids = set(EventParticipant.objects.filter(user=request.user, status='approved').values_list('event_id', flat=True))
        liked_ids = set(EventLike.objects.filter(user=request.user).values_list('event_id', flat=True))
        saved_ids = set(EventSave.objects.filter(user=request.user).values_list('event_id', flat=True))
        for e in events:
            e.user_joined = e.id in joined_ids
            e.user_liked = e.id in liked_ids
            e.user_saved = e.id in saved_ids

        categories = EventCategory.objects.all()

        # Upcoming joined events for right sidebar
        from django.utils import timezone as tz
        upcoming = Event.objects.filter(
            participants__user=request.user,
            participants__status='approved',
            start_datetime__gte=tz.now(),
            status='published',
        ).select_related('category').order_by('start_datetime')[:5]

        # Suggested users: active users not yet followed, not friends
        from apps.accounts.models import User as AppUser
        from apps.social.models import Follow
        following_ids = set(Follow.objects.filter(follower=request.user).values_list('following_id', flat=True))
        following_ids.add(request.user.id)
        suggested = AppUser.objects.filter(
            is_active=True
        ).exclude(id__in=following_ids).select_related('profile').order_by('?')[:5]

        user_profile = None
        followers_count = 0
        following_count = 0
        try:
            user_profile = request.user.profile
            from apps.social.models import Follow as FollowModel
            followers_count = FollowModel.objects.filter(following=request.user).count()
            following_count = FollowModel.objects.filter(follower=request.user).count()
        except Exception:
            pass

        # Events happening right now
        live_events = Event.objects.filter(
            status='published',
            start_datetime__lte=tz.now(),
            end_datetime__gte=tz.now(),
        ).select_related('host', 'host__profile', 'category').annotate(pcount=Count('participants')).order_by('-pcount')[:3]

        return render(request, 'feed/feed.html', {
            'events': events,
            'tab': tab,
            'categories': categories,
            'category_slug': category_slug,
            'upcoming': upcoming,
            'suggested': suggested,
            'user_profile': user_profile,
            'followers_count': followers_count,
            'following_count': following_count,
            'live_events': live_events,
        })


class EventListView(View):
    def get(self, request):
        qs = Event.objects.filter(status='published').select_related('host', 'host__profile', 'category')
        category = request.GET.get('category')
        if category:
            qs = qs.filter(category__slug=category)
        q = request.GET.get('q')
        if q:
            qs = qs.filter(Q(title__icontains=q) | Q(description__icontains=q))
        events = qs.order_by('-created_at')[:50]
        categories = EventCategory.objects.all()
        return render(request, 'events/event_list.html', {'events': events, 'categories': categories})


class EventDetailView(View):
    def get(self, request, pk):
        event = get_object_or_404(
            Event.objects.select_related('host', 'host__profile', 'category', 'subcategory'),
            pk=pk
        )
        event.view_count += 1
        event.save(update_fields=['view_count'])

        participants = event.participants.filter(status='approved').select_related('user', 'user__profile')[:20]
        waitlist = event.participants.filter(status='waitlist').select_related('user', 'user__profile')[:10]
        reviews = event.reviews.select_related('reviewer', 'reviewer__profile')[:10]
        gallery = event.gallery.select_related('uploaded_by')[:20]
        co_hosts = event.co_hosts.select_related('user', 'user__profile')

        user_joined = False
        user_liked = False
        user_saved = False
        user_participant = None
        if request.user.is_authenticated:
            user_participant = event.participants.filter(user=request.user).first()
            user_joined = user_participant and user_participant.status == 'approved'
            user_liked = event.likes.filter(user=request.user).exists()
            user_saved = event.saves.filter(user=request.user).exists()

        # Related events: same category first, fall back to any public events
        related_base = Event.objects.filter(status='published', privacy='public').exclude(pk=pk).select_related('host', 'host__profile', 'category')
        if event.category:
            related_events = list(related_base.filter(category=event.category).order_by('-created_at')[:4])
        else:
            related_events = []
        if len(related_events) < 4:
            extra = related_base.exclude(pk__in=[e.pk for e in related_events]).order_by('-created_at')[:4 - len(related_events)]
            related_events += list(extra)

        # Average review rating
        from django.db.models import Avg
        avg_rating = event.reviews.aggregate(avg=Avg('rating'))['avg']

        # Host stats
        host_event_count = Event.objects.filter(host=event.host, status='published').count()

        # Capacity percentage for bar
        capacity_pct = 0
        if event.capacity and event.capacity > 0:
            capacity_pct = min(100, round(event.participant_count / event.capacity * 100))

        context = {
            'event': event,
            'participants': participants,
            'waitlist': waitlist,
            'reviews': reviews,
            'gallery': gallery,
            'co_hosts': co_hosts,
            'user_joined': user_joined,
            'user_liked': user_liked,
            'user_saved': user_saved,
            'user_participant': user_participant,
            'participant_count': event.participant_count,
            'related_events': related_events,
            'avg_rating': round(avg_rating, 1) if avg_rating else None,
            'host_event_count': host_event_count,
            'capacity_pct': capacity_pct,
        }
        return render(request, 'events/event_detail.html', context)


class EventCreateView(LoginRequiredMixin, View):
    login_url = '/accounts/login/'

    def get(self, request):
        categories = EventCategory.objects.prefetch_related('subcategories').all()
        # Pre-fill co-hosts from group chat redirect (?cohosts=user1,user2)
        from apps.accounts.models import User as UserModel
        prefill_cohosts = []
        cohosts_param = request.GET.get('cohosts', '')
        if cohosts_param:
            usernames = [u.strip() for u in cohosts_param.split(',') if u.strip()]
            prefill_cohosts = list(UserModel.objects.filter(username__in=usernames).select_related('profile'))
        return render(request, 'events/event_create.html', {
            'categories': categories,
            'step': int(request.GET.get('step', 1)),
            'prefill_cohosts': prefill_cohosts,
            'from_group': request.GET.get('group', ''),
        })

    def post(self, request):
        from django.utils.dateparse import parse_datetime
        categories = EventCategory.objects.prefetch_related('subcategories').all()
        try:
            event = Event.objects.create(
                host=request.user,
                title=request.POST.get('title', '').strip(),
                description=request.POST.get('description', '').strip(),
                category_id=request.POST.get('category') or None,
                subcategory_id=request.POST.get('subcategory') or None,
                start_datetime=parse_datetime(request.POST.get('start_datetime', '')) or timezone.now(),
                end_datetime=parse_datetime(request.POST.get('end_datetime', '')) or timezone.now(),
                timezone=request.POST.get('timezone', 'UTC'),
                latitude=float(request.POST.get('latitude', 0) or 0) or None,
                longitude=float(request.POST.get('longitude', 0) or 0) or None,
                address=request.POST.get('address', '').strip(),
                location_name=request.POST.get('location_name', '').strip(),
                is_online=request.POST.get('is_online') == 'on',
                online_link=request.POST.get('online_link', '').strip(),
                privacy=request.POST.get('privacy', 'public'),
                requires_approval=request.POST.get('requires_approval') == 'on',
                event_type=request.POST.get('event_type', 'free'),
                capacity=int(request.POST.get('capacity', 0)) or None,
                has_waitlist=request.POST.get('has_waitlist') == 'on',
                rules=request.POST.get('rules', '').strip(),
                is_indoor=request.POST.get('is_indoor', 'on') == 'on',
                status='published' if request.POST.get('action') == 'publish' else 'draft',
            )
            if 'cover_image' in request.FILES:
                event.cover_image = request.FILES['cover_image']
                event.save()
            # Update host profile stats
            try:
                request.user.profile.hosted_events_count += 1
                request.user.profile.save(update_fields=['hosted_events_count'])
            except Exception:
                pass
            return redirect('events:event_detail', pk=event.pk)
        except Exception as e:
            return render(request, 'events/event_create.html', {'categories': categories, 'error': str(e), 'step': 1, 'data': request.POST})


class EventEditView(LoginRequiredMixin, View):
    login_url = '/accounts/login/'

    def get(self, request, pk):
        event = get_object_or_404(Event, pk=pk, host=request.user)
        categories = EventCategory.objects.prefetch_related('subcategories').all()
        return render(request, 'events/event_edit.html', {'event': event, 'categories': categories})

    def post(self, request, pk):
        event = get_object_or_404(Event, pk=pk, host=request.user)
        from django.utils.dateparse import parse_datetime
        event.title = request.POST.get('title', event.title).strip()
        event.description = request.POST.get('description', event.description).strip()
        event.start_datetime = parse_datetime(request.POST.get('start_datetime', '')) or event.start_datetime
        event.end_datetime = parse_datetime(request.POST.get('end_datetime', '')) or event.end_datetime
        event.address = request.POST.get('address', event.address)
        event.location_name = request.POST.get('location_name', event.location_name)
        event.privacy = request.POST.get('privacy', event.privacy)
        event.rules = request.POST.get('rules', event.rules)
        if request.POST.get('latitude'):
            event.latitude = float(request.POST.get('latitude'))
        if request.POST.get('longitude'):
            event.longitude = float(request.POST.get('longitude'))
        if 'cover_image' in request.FILES:
            event.cover_image = request.FILES['cover_image']
        event.status = 'published' if request.POST.get('action') == 'publish' else event.status
        event.save()
        return redirect('events:event_detail', pk=event.pk)


class EventDeleteView(LoginRequiredMixin, View):
    login_url = '/accounts/login/'

    def post(self, request, pk):
        event = get_object_or_404(Event, pk=pk, host=request.user)
        event.delete()
        return redirect('events:feed')


class EventJoinView(LoginRequiredMixin, View):
    login_url = '/accounts/login/'

    def post(self, request, pk):
        event = get_object_or_404(Event, pk=pk)
        if event.host == request.user:
            return JsonResponse({'error': 'You are the host'}, status=400)
        if event.is_full and not event.has_waitlist:
            return JsonResponse({'error': 'Event is full'}, status=400)

        participant, created = EventParticipant.objects.get_or_create(
            event=event, user=request.user,
            defaults={'status': 'waitlist' if event.is_full else ('pending' if event.requires_approval else 'approved')}
        )
        if not created:
            return JsonResponse({'error': 'Already joined'}, status=400)

        if participant.status == 'approved':
            try:
                request.user.profile.joined_events_count += 1
                request.user.profile.save(update_fields=['joined_events_count'])
            except Exception:
                pass
        return JsonResponse({'status': participant.status, 'participant_count': event.participant_count})


class EventLeaveView(LoginRequiredMixin, View):
    login_url = '/accounts/login/'

    def post(self, request, pk):
        event = get_object_or_404(Event, pk=pk)
        EventParticipant.objects.filter(event=event, user=request.user).delete()
        try:
            if request.user.profile.joined_events_count > 0:
                request.user.profile.joined_events_count -= 1
                request.user.profile.save(update_fields=['joined_events_count'])
        except Exception:
            pass
        return JsonResponse({'success': True, 'participant_count': event.participant_count})


class EventLikeView(LoginRequiredMixin, View):
    login_url = '/accounts/login/'

    def post(self, request, pk):
        event = get_object_or_404(Event, pk=pk)
        like, created = EventLike.objects.get_or_create(event=event, user=request.user)
        if not created:
            like.delete()
            event.like_count = max(0, event.like_count - 1)
            event.save(update_fields=['like_count'])
            return JsonResponse({'liked': False, 'count': event.like_count})
        event.like_count += 1
        event.save(update_fields=['like_count'])
        return JsonResponse({'liked': True, 'count': event.like_count})


class EventSaveView(LoginRequiredMixin, View):
    login_url = '/accounts/login/'

    def post(self, request, pk):
        event = get_object_or_404(Event, pk=pk)
        save, created = EventSave.objects.get_or_create(event=event, user=request.user)
        if not created:
            save.delete()
            event.save_count = max(0, event.save_count - 1)
            event.save(update_fields=['save_count'])
            return JsonResponse({'saved': False})
        event.save_count += 1
        event.save(update_fields=['save_count'])
        return JsonResponse({'saved': True})


class EventCheckinView(LoginRequiredMixin, View):
    login_url = '/accounts/login/'

    def post(self, request, pk):
        event = get_object_or_404(Event, pk=pk)
        try:
            participant = EventParticipant.objects.get(event=event, user=request.user, status='approved')
            participant.checked_in = True
            participant.checked_in_at = timezone.now()
            participant.save()
            return JsonResponse({'success': True})
        except EventParticipant.DoesNotExist:
            return JsonResponse({'error': 'Not a participant'}, status=400)
