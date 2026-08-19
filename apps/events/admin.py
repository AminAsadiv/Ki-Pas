from django.contrib import admin
from .models import Event, EventCategory, EventSubcategory, EventParticipant, Tag

@admin.register(EventCategory)
class EventCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'icon', 'order']
    prepopulated_fields = {'slug': ('name',)}

@admin.register(EventSubcategory)
class EventSubcategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'slug']
    list_filter = ['category']

@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ['title', 'host', 'category', 'status', 'start_datetime', 'privacy']
    list_filter = ['status', 'privacy', 'category', 'event_type']
    search_fields = ['title', 'host__username']

@admin.register(EventParticipant)
class EventParticipantAdmin(admin.ModelAdmin):
    list_display = ['user', 'event', 'status', 'joined_at', 'checked_in']

@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    prepopulated_fields = {'slug': ('name',)}
