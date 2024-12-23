from django.db import models

from apps.base.model_fields import TimeZoneField


class Event(models.Model):
    name = models.CharField(max_length=255)
    timezone = TimeZoneField()
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()

    def __str__(self):
        return self.name
