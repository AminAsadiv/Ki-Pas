from django.db import models
from django.conf import settings


class XPTransaction(models.Model):
    REASON_CHOICES = [
        ('hosted_event_large', 'Hosted Event (10+ attendees, 4+ stars)'),
        ('hosted_event_medium', 'Hosted Event (5-9 attendees)'),
        ('attended_event', 'Attended Event'),
        ('left_review', 'Left a Review'),
        ('received_5star', 'Received 5-star Review'),
        ('first_event_hosted', 'First Event Hosted Bonus'),
        ('login_streak', '7-day Login Streak'),
        ('profile_complete', 'Profile 100% Complete'),
        ('badge_earned', 'Badge Earned'),
        ('invited_friend', 'Invited Friend Who Joined'),
        ('verified_host', 'Verified Host Status'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='xp_transactions')
    amount = models.IntegerField()
    reason = models.CharField(max_length=50, choices=REASON_CHOICES)
    event = models.ForeignKey('events.Event', on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']


LEVEL_THRESHOLDS = [0, 200, 600, 1500, 3500, 7000, 14000, 28000, 55000, 100000]
LEVEL_TITLES = ['Newcomer', 'Explorer', 'Connector', 'Organizer', 'Host',
                'Veteran', 'Champion', 'Legend', 'Icon', 'KIPAS Elite']


class Badge(models.Model):
    CONDITION_CHOICES = [
        ('host_count', 'Events Hosted'), ('attend_count', 'Events Attended'),
        ('rating_avg', 'Average Rating'), ('friend_count', 'Friend Count'),
        ('review_count', 'Reviews Given'), ('xp_total', 'Total XP'),
    ]

    name = models.CharField(max_length=100)
    description = models.TextField()
    icon = models.CharField(max_length=50)
    xp_reward = models.IntegerField(default=0)
    condition_type = models.CharField(max_length=30, choices=CONDITION_CHOICES)
    condition_value = models.IntegerField()
    color = models.CharField(max_length=7, default='#40FFA7')

    def __str__(self):
        return self.name


class UserBadge(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='badges')
    badge = models.ForeignKey(Badge, on_delete=models.CASCADE)
    earned_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'badge')
        ordering = ['-earned_at']


class LoginStreak(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='login_streak')
    current_streak = models.IntegerField(default=0)
    longest_streak = models.IntegerField(default=0)
    last_login_date = models.DateField(null=True, blank=True)
