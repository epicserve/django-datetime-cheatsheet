"""
Tests for basic datetime operations in Django.
"""
import datetime
from datetime import date, datetime, time, timezone, timedelta
from zoneinfo import ZoneInfo

from django.conf import settings
from django.test import TestCase
from django.utils import timezone as dj_tz

from apps.events.models import Event
from model_bakery import baker

utc = timezone.utc


class TestDateTimeBasics(TestCase):
    def test_datetime_basics(self):
        # Get the current timezone, the current timezone is based on the TIME_ZONE setting in Django settings.
        current_tz = dj_tz.get_current_timezone()
        assert str(current_tz) == settings.TIME_ZONE

        # Get the current datetime in UTC
        now = dj_tz.now()
        assert now.tzinfo == utc

        # Check if a datetime object is naive or aware. Naive, meaning it doesn't have a timezone, and aware, meaning
        # it has a timezone.
        naive_datetime = datetime(2024, 4, 7, 14, 30)
        assert dj_tz.is_naive(naive_datetime) is True
        assert dj_tz.is_aware(naive_datetime) is False

        # Make a naive datetime aware
        aware_datetime = dj_tz.make_aware(naive_datetime)
        assert aware_datetime.tzinfo == current_tz
        assert dj_tz.is_naive(aware_datetime) is False
        assert dj_tz.is_aware(aware_datetime) is True

        # Create a fixed datetime in UTC for demonstration purposes
        utc_dt = datetime(2024, 10, 1, 13, 30, tzinfo=utc)
        assert utc_dt.tzinfo == utc

        # Get the current datetime in the local timezone
        local_dt = dj_tz.localtime(utc_dt)
        assert local_dt.tzinfo == ZoneInfo("America/Chicago")

        # Convert another local datetime to a different timezone
        mountain_datetime = dj_tz.localtime(
            local_dt, timezone=ZoneInfo("America/Denver")
        )
        assert mountain_datetime.tzinfo == ZoneInfo("America/Denver")

        # Avoid bugs with dates by using Django's localdate function
        # 6 p.m. on January 1st in the local timezone is 12 a.m. on January 2nd in UTC
        local_dt = datetime(2024, 1, 1, 18, 0, tzinfo=ZoneInfo("America/Chicago"))
        utc_dt_next_day = dj_tz.localtime(local_dt, timezone=utc)
        assert utc_dt_next_day.date() != date(2024, 1, 1)
        assert utc_dt_next_day.date() == date(2024, 1, 2)
        assert dj_tz.localdate(utc_dt_next_day) == date(2024, 1, 1)

    def test_timezone_activation(self):
        """
        Change the active timezone for the current thread

        It should be noted that we use this method for web requests to set the time_zone to the users timezone
        using our own Django middleware (apps.base.middleware.TimezoneMiddleware). I'm guessing we have some bugs in
        jobs that send emails because I bet we forget to set the timezone in the job to the user's timezone.
        """
        assert dj_tz.get_current_timezone_name() == "America/Chicago"
        dj_tz.activate(ZoneInfo("America/New_York"))
        assert dj_tz.get_current_timezone_name() == "America/New_York"
        dj_tz.deactivate()  # Reset the active timezone
        assert dj_tz.get_current_timezone_name() == "America/Chicago"

    def test_timezone_override(self):
        # Use override to temporarily save a model's datetime in a different timezone
        with dj_tz.override(ZoneInfo("America/Los_Angeles")):
            event_start_time = dj_tz.make_aware(datetime(2024, 1, 1, 22, 30))
            event_end_time = event_start_time + timedelta(hours=1)
            event = baker.make("events.Event")
            event.start_time = event_start_time
            event.end_time = event_end_time
            event.save()

        event.refresh_from_db()
        assert (
            dj_tz.localtime(event.start_time, ZoneInfo("America/Los_Angeles"))
            == event_start_time
        )

    def test_datetime_combine(self):
        """
        Combine a date object with a time object to create a datetime object

        It should be noted that you can use Django's SplitDateTimeField if you want to combine a date and time in a
        form that is using separate fields.
        """
        datetime_obj = dj_tz.make_aware(
            datetime.combine(date(2024, 1, 1), time(22, 30))
        )
        assert datetime_obj.tzinfo == dj_tz.get_current_timezone() 