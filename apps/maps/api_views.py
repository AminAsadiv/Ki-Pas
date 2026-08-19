from django.http import JsonResponse
from django.views import View
from apps.events.models import Event
from django.conf import settings


class MapEventsAPIView(View):
    def get(self, request):
        qs = Event.objects.filter(status='published', latitude__isnull=False, longitude__isnull=False)

        category = request.GET.get('category')
        if category:
            qs = qs.filter(category__slug=category)

        try:
            sw_lat = float(request.GET.get('sw_lat', -90))
            sw_lng = float(request.GET.get('sw_lng', -180))
            ne_lat = float(request.GET.get('ne_lat', 90))
            ne_lng = float(request.GET.get('ne_lng', 180))
            qs = qs.filter(latitude__gte=sw_lat, latitude__lte=ne_lat, longitude__gte=sw_lng, longitude__lte=ne_lng)
        except (TypeError, ValueError):
            pass

        events = []
        for e in qs.select_related('category', 'host')[:100]:
            events.append({
                'id': e.id,
                'title': e.title,
                'latitude': e.latitude,
                'longitude': e.longitude,
                'category_name': e.category.name if e.category else '',
                'category_slug': e.category.slug if e.category else '',
                'event_type': e.event_type,
                'start_datetime': e.start_datetime.isoformat(),
                'location_name': e.location_name,
                'address': e.address,
                'participant_count': e.participant_count,
                'capacity': e.capacity,
                'cover_image': e.cover_image.url if e.cover_image else None,
            })
        return JsonResponse({'events': events})
