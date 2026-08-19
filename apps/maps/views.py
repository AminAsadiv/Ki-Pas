from django.shortcuts import render
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views import View
from apps.events.models import Event, EventCategory


class MapView(View):
    def get(self, request):
        categories = EventCategory.objects.all()
        # URL params for pre-centering (e.g. from event detail "View on Map")
        lat = request.GET.get('lat', '')
        lng = request.GET.get('lng', '')
        return render(request, 'map/map.html', {
            'categories': categories,
            'initial_lat': lat,
            'initial_lng': lng,
        })
