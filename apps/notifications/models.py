from django.db import models
from django.conf import settings


class Notification(models.Model):
    TYPE_CHOICES = [
        ('friend_request', 'Friend Request'), ('friend_accepted', 'Friend Accepted'),
        ('event_invitation', 'Event Invitation'), ('event_reminder', 'Event Reminder'),
        ('event_update', 'Event Update'), ('event_cancelled', 'Event Cancelled'),
        ('new_message', 'New Message'), ('like', 'Like'), ('comment', 'Comment'),
        ('review_received', 'Review Received'), ('badge_earned', 'Badge Earned'),
        ('level_up', 'Level Up'), ('xp_earned', 'XP Earned'),
        ('sos_alert', 'SOS Alert'), ('report_resolved', 'Report Resolved'),
        ('account_warning', 'Account Warning'),
    ]

    recipient = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='notifications')
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='actions')
    notification_type = models.CharField(max_length=30, choices=TYPE_CHOICES)
    title = models.CharField(max_length=200)
    message = models.TextField()
    link = models.CharField(max_length=500, blank=True)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    # Generic FK for the related object
    content_type = models.CharField(max_length=50, blank=True)
    object_id = models.CharField(max_length=50, blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Notification for {self.recipient.username}: {self.title}"


class NotificationPreference(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='notification_pref')
    email_friend_requests = models.BooleanField(default=True)
    email_event_reminders = models.BooleanField(default=True)
    email_event_updates = models.BooleanField(default=True)
    email_new_messages = models.BooleanField(default=False)
    email_weekly_digest = models.BooleanField(default=True)
    push_friend_requests = models.BooleanField(default=True)
    push_event_reminders = models.BooleanField(default=True)
    push_new_messages = models.BooleanField(default=True)
    push_likes = models.BooleanField(default=True)
