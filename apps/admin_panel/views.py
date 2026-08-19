from django.shortcuts import render
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views import View
from apps.accounts.models import User
from apps.events.models import Event
from apps.moderation.models import Report


class AdminRequiredMixin(LoginRequiredMixin):
    login_url = '/accounts/login/'

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_staff:
            from django.http import Http404
            raise Http404
        return super().dispatch(request, *args, **kwargs)


class AdminDashboardView(AdminRequiredMixin, View):
    def get(self, request):
        stats = {
            'total_users': User.objects.count(),
            'active_users': User.objects.filter(is_active=True).count(),
            'total_events': Event.objects.count(),
            'published_events': Event.objects.filter(status='published').count(),
            'open_reports': Report.objects.filter(status='pending').count(),
        }
        recent_users = User.objects.order_by('-date_joined')[:10]
        recent_events = Event.objects.order_by('-created_at')[:10]
        return render(request, 'admin_panel/dashboard.html', {'stats': stats, 'recent_users': recent_users, 'recent_events': recent_events})


class AdminUsersView(AdminRequiredMixin, View):
    def get(self, request):
        users = User.objects.select_related('profile').order_by('-date_joined')[:100]
        return render(request, 'admin_panel/users.html', {'users': users})


class AdminEventsView(AdminRequiredMixin, View):
    def get(self, request):
        events = Event.objects.select_related('host', 'category').order_by('-created_at')[:100]
        return render(request, 'admin_panel/events.html', {'events': events})


class AdminReportsView(AdminRequiredMixin, View):
    def get(self, request):
        reports = Report.objects.filter(status='pending').select_related('reporter').order_by('-severity_score', '-created_at')[:50]
        return render(request, 'admin_panel/reports.html', {'reports': reports})
