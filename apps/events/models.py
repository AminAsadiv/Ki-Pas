from django.db import models
from django.conf import settings


class Tag(models.Model):
    name = models.CharField(max_length=50, unique=True)
    slug = models.SlugField(unique=True)

    def __str__(self):
        return self.name


class EventCategory(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)
    icon = models.CharField(max_length=50)
    color = models.CharField(max_length=7, default='#40FFA7')
    order = models.IntegerField(default=0)

    class Meta:
        ordering = ['order', 'name']
        verbose_name_plural = 'Event Categories'

    def __str__(self):
        return self.name


class EventSubcategory(models.Model):
    category = models.ForeignKey(EventCategory, on_delete=models.CASCADE, related_name='subcategories')
    name = models.CharField(max_length=100)
    slug = models.SlugField()
    icon = models.CharField(max_length=50, blank=True)

    class Meta:
        unique_together = ('category', 'slug')

    def __str__(self):
        return f"{self.category.name} > {self.name}"


class Event(models.Model):
    PRIVACY_CHOICES = [
        ('public', 'Public'), ('friends', 'Friends Only'),
        ('private', 'Private'), ('password', 'Password Protected'),
    ]
    EVENT_TYPE_CHOICES = [
        ('free', 'Free'), ('paid', 'Paid'),
        ('recurring', 'Recurring'), ('one_time', 'One Time'),
    ]
    STATUS_CHOICES = [
        ('draft', 'Draft'), ('published', 'Published'), ('ongoing', 'Ongoing'),
        ('completed', 'Completed'), ('cancelled', 'Cancelled'), ('postponed', 'Postponed'),
    ]

    host = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='hosted_events')
    title = models.CharField(max_length=200)
    description = models.TextField()
    category = models.ForeignKey(EventCategory, on_delete=models.SET_NULL, null=True, related_name='events')
    subcategory = models.ForeignKey(EventSubcategory, on_delete=models.SET_NULL, null=True, blank=True)
    tags = models.ManyToManyField(Tag, blank=True)
    cover_image = models.ImageField(upload_to='event-covers/', blank=True, null=True)
    rules = models.TextField(blank=True)

    start_datetime = models.DateTimeField()
    end_datetime = models.DateTimeField()
    timezone = models.CharField(max_length=50, default='UTC')
    registration_deadline = models.DateTimeField(null=True, blank=True)
    is_recurring = models.BooleanField(default=False)
    recurrence_rule = models.CharField(max_length=200, blank=True)

    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    address = models.TextField(blank=True)
    location_name = models.CharField(max_length=200, blank=True)
    is_online = models.BooleanField(default=False)
    online_link = models.URLField(blank=True)
    is_indoor = models.BooleanField(default=True)

    privacy = models.CharField(max_length=20, choices=PRIVACY_CHOICES, default='public')
    password_hash = models.CharField(max_length=200, blank=True)
    requires_approval = models.BooleanField(default=False)
    event_type = models.CharField(max_length=20, choices=EVENT_TYPE_CHOICES, default='free')
    is_verified_host_event = models.BooleanField(default=False)

    capacity = models.IntegerField(null=True, blank=True)
    has_waitlist = models.BooleanField(default=True)

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')

    view_count = models.IntegerField(default=0)
    like_count = models.IntegerField(default=0)
    save_count = models.IntegerField(default=0)
    share_count = models.IntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.title

    @property
    def participant_count(self):
        return self.participants.filter(status='approved').count()

    @property
    def is_full(self):
        if self.capacity is None:
            return False
        return self.participant_count >= self.capacity


class EventParticipant(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'), ('approved', 'Approved'),
        ('waitlist', 'Waitlist'), ('removed', 'Removed'),
    ]

    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='participants')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='event_participations')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='approved')
    joined_at = models.DateTimeField(auto_now_add=True)
    checked_in = models.BooleanField(default=False)
    checked_in_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ('event', 'user')

    def __str__(self):
        return f"{self.user.username} @ {self.event.title}"


class EventCoHost(models.Model):
    ROLE_CHOICES = [
        ('cohost', 'Co-Host'), ('organizer', 'Organizer'),
        ('moderator', 'Moderator'), ('volunteer', 'Volunteer'), ('staff', 'Staff'),
    ]

    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='co_hosts')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='cohost')

    class Meta:
        unique_together = ('event', 'user')


class EventLike(models.Model):
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='likes')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('event', 'user')


class EventSave(models.Model):
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='saves')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('event', 'user')


class EventGallery(models.Model):
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='gallery')
    uploaded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    image = models.ImageField(upload_to='event-gallery/')
    caption = models.CharField(max_length=200, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
