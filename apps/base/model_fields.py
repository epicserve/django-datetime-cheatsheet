import zoneinfo

from django.db import models
from django.utils import timezone


def get_valid_timezones():
    return sorted([(tz, tz) for tz in zoneinfo.available_timezones()])


class TimeZoneField(models.CharField):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault("max_length", 100)
        kwargs.setdefault("choices", get_valid_timezones())
        kwargs.setdefault("default", timezone.get_current_timezone_name())
        super().__init__(*args, **kwargs)
