from zoneinfo import ZoneInfo

from django.db import models
from django.utils import timezone

from apps.base.model_fields import TimeZoneField


class Event(models.Model):
    name = models.CharField(max_length=255)
    timezone = TimeZoneField()
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()

    def __str__(self):
        return self.name

    def display_start_time(self):
        return timezone.make_naive(self.start_time, ZoneInfo(self.timezone))

    def display_end_time(self):
        return timezone.make_naive(self.end_time, ZoneInfo(self.timezone))
