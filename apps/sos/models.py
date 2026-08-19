from django.db import models
from django.conf import settings


class SOSRequest(models.Model):
    STATUS_CHOICES = [('active', 'Active'), ('resolved', 'Resolved'), ('expired', 'Expired')]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='sos_requests')
    latitude = models.FloatField()
    longitude = models.FloatField()
    message = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    created_at = models.DateTimeField(auto_now_add=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    auto_expires_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']


class SOSHelper(models.Model):
    sos_request = models.ForeignKey(SOSRequest, on_delete=models.CASCADE, related_name='helpers')
    helper = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    responded_at = models.DateTimeField(auto_now_add=True)
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)

    class Meta:
        unique_together = ('sos_request', 'helper')
