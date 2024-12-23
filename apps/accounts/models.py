from django.contrib.auth.models import AbstractUser
from ..base.model_fields import TimeZoneField


class User(AbstractUser):
    timezone = TimeZoneField()
