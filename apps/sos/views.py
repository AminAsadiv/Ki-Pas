from django.shortcuts import render
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views import View


class SOSView(LoginRequiredMixin, View):
    login_url = '/accounts/login/'

    def get(self, request):
        from .models import SOSRequest
        active_sos = SOSRequest.objects.filter(status='active').select_related('user', 'user__profile')[:20]
        return render(request, 'sos/sos.html', {'active_sos': active_sos})
