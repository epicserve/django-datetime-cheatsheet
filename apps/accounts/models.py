import zoneinfo

from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone


def get_valid_timezones():
    return sorted([(tz, tz) for tz in zoneinfo.available_timezones()])


class User(AbstractUser):
    timezone = models.CharField(
        max_length=100,
        choices=get_valid_timezones(),
        default=timezone.get_current_timezone_name(),
    )
