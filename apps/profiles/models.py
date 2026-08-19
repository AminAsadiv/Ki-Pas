from django.db import models
from django.conf import settings


class Profile(models.Model):
    WHO_CAN_CHOICES = [('everyone', 'Everyone'), ('friends', 'Friends Only'), ('nobody', 'Nobody')]

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='profile')
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)
    cover_photo = models.ImageField(upload_to='covers/', blank=True, null=True)
    full_name = models.CharField(max_length=100, blank=True)
    bio = models.TextField(max_length=500, blank=True)
    city = models.CharField(max_length=100, blank=True)
    country = models.CharField(max_length=100, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    language = models.CharField(max_length=10, default='en')
    website = models.URLField(blank=True)
    instagram = models.CharField(max_length=100, blank=True)
    twitter = models.CharField(max_length=100, blank=True)
    linkedin = models.CharField(max_length=100, blank=True)
    is_online = models.BooleanField(default=False)
    last_seen = models.DateTimeField(null=True, blank=True)
    is_public = models.BooleanField(default=True)
    show_email = models.BooleanField(default=False)
    show_friends = models.BooleanField(default=True)
    who_can_message = models.CharField(max_length=20, choices=WHO_CAN_CHOICES, default='everyone')
    who_can_friend = models.CharField(max_length=20, choices=[('everyone', 'Everyone'), ('nobody', 'Nobody')], default='everyone')
    dark_mode = models.BooleanField(default=True)
    reputation_score = models.FloatField(default=0)
    xp = models.IntegerField(default=0)
    level = models.IntegerField(default=1)
    hosted_events_count = models.IntegerField(default=0)
    joined_events_count = models.IntegerField(default=0)
    average_rating = models.FloatField(default=0)
    is_verified_host = models.BooleanField(default=False)
    favorite_categories = models.ManyToManyField('events.EventCategory', blank=True, related_name='interested_profiles')
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    share_location = models.BooleanField(default=False)

    def __str__(self):
        return f"Profile of {self.user.username}"

    @property
    def level_title(self):
        titles = {1: 'Newcomer', 2: 'Explorer', 3: 'Connector', 4: 'Organizer',
                  5: 'Host', 6: 'Veteran', 7: 'Champion', 8: 'Legend', 9: 'Icon', 10: 'KIPAS Elite'}
        return titles.get(self.level, 'Newcomer')

    @property
    def xp_to_next_level(self):
        thresholds = [0, 200, 600, 1500, 3500, 7000, 14000, 28000, 55000, 100000]
        if self.level >= 10:
            return 0
        return thresholds[self.level] - self.xp

    @property
    def level_progress_pct(self):
        thresholds = [0, 200, 600, 1500, 3500, 7000, 14000, 28000, 55000, 100000]
        if self.level >= 10:
            return 100
        current_threshold = thresholds[self.level - 1]
        next_threshold = thresholds[self.level]
        return int((self.xp - current_threshold) / (next_threshold - current_threshold) * 100)
