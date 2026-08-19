from django.db import models
from django.conf import settings


class Report(models.Model):
    REPORT_TYPE_CHOICES = [
        ('user', 'User'), ('event', 'Event'), ('message', 'Message'), ('review', 'Review'),
    ]
    REASON_CHOICES = [
        ('spam', 'Spam'), ('harassment', 'Harassment'), ('hate_speech', 'Hate Speech'),
        ('violence', 'Violence'), ('misinformation', 'Misinformation'),
        ('inappropriate', 'Inappropriate Content'), ('other', 'Other'),
    ]
    STATUS_CHOICES = [
        ('pending', 'Pending'), ('reviewing', 'Reviewing'),
        ('resolved', 'Resolved'), ('dismissed', 'Dismissed'),
    ]

    reporter = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='reports_filed')
    report_type = models.CharField(max_length=20, choices=REPORT_TYPE_CHOICES)
    reason = models.CharField(max_length=30, choices=REASON_CHOICES)
    description = models.TextField(blank=True)
    object_id = models.CharField(max_length=50)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    severity_score = models.IntegerField(default=1)
    resolved_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='resolved_reports')
    resolved_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-severity_score', '-created_at']


class UserWarning(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='warnings')
    issued_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='issued_warnings')
    reason = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)


class UserBan(models.Model):
    BAN_TYPE_CHOICES = [('temp', 'Temporary'), ('permanent', 'Permanent'), ('shadow', 'Shadow Ban')]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='bans')
    ban_type = models.CharField(max_length=20, choices=BAN_TYPE_CHOICES)
    reason = models.TextField()
    banned_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='issued_bans')
    expires_at = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
