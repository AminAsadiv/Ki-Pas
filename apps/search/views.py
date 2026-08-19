from django.shortcuts import render
from django.views import View
from django.db.models import Q
from apps.events.models import Event, EventCategory
from apps.accounts.models import User


class SearchView(View):
    def get(self, request):
        q = request.GET.get('q', '').strip()
        tab = request.GET.get('tab', 'all')
        category = request.GET.get('category', '')
        event_type = request.GET.get('type', '')
        sort = request.GET.get('sort', 'relevance')

        events = []
        users = []

        if q or category or event_type:
            event_qs = Event.objects.filter(status='published').select_related('host', 'host__profile', 'category')
            if q:
                event_qs = event_qs.filter(
                    Q(title__icontains=q) | Q(description__icontains=q)
                    | Q(location_name__icontains=q) | Q(category__name__icontains=q)
                )
            if category:
                event_qs = event_qs.filter(category__slug=category)
            if event_type:
                event_qs = event_qs.filter(event_type=event_type)

            if sort == 'date':
                event_qs = event_qs.order_by('start_datetime')
            elif sort == 'popular':
                event_qs = event_qs.order_by('-like_count', '-view_count')
            elif sort == 'newest':
                event_qs = event_qs.order_by('-created_at')
            else:
                event_qs = event_qs.order_by('-view_count', '-like_count')

            if tab in ('all', 'events'):
                events = list(event_qs[:24])

            if tab in ('all', 'people') and q:
                users = list(User.objects.filter(
                    Q(username__icontains=q) | Q(profile__full_name__icontains=q)
                    | Q(profile__city__icontains=q),
                    is_active=True,
                ).select_related('profile').order_by('username')[:16])

        categories = EventCategory.objects.all()
        trending_terms = ['Running', 'Tech Talks', 'Photography', 'Board Games', 'Yoga', 'Community Cleanup', 'Startup Pitch', 'Food Tour', 'Music Night', 'Art Walk', 'Hiking', 'Coding Bootcamp']
        return render(request, 'search/search.html', {
            'q': q,
            'tab': tab,
            'category': category,
            'event_type': event_type,
            'sort': sort,
            'events': events,
            'users': users,
            'categories': categories,
            'trending_terms': trending_terms,
        })
