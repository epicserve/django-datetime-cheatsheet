"""
Basic datetime operations in Django

Basic operations with datetime objects in Django, including timezone handling and conversions.
"""

from datetime import date, datetime, time, timezone, timedelta
from zoneinfo import ZoneInfo

from django.conf import settings
from django.test import TestCase
from django.utils import timezone as dj_tz

from model_bakery import baker

utc = timezone.utc


class TestDateTimeBasics(TestCase):
    def test_datetime_basics(self):
        """
        The following code demonstrates how to work with timezone-aware and naive datetime objects, how to get the
        current time in different timezones, and how to convert between timezones. `settings.TIME_ZONE` is set to
        `"America/Chicago"` in the Django settings, `utc` equals `datetime.timezone.utc`, and `dj_tz` equals
        `django.utils.timezone`.
        """
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

        # Convert a UTC datetime to a local datetime object
        local_dt = dj_tz.localtime(utc_dt)
        assert local_dt.tzinfo == ZoneInfo("America/Chicago")

        # Convert a local datetime object to a different timezone
        mountain_datetime = dj_tz.localtime(
            local_dt, timezone=ZoneInfo("America/Denver")
        )
        assert mountain_datetime.tzinfo == ZoneInfo("America/Denver")

        # Avoid bugs with dates by using Django's localdate function
        # 6 p.m. on January 1st in the local timezone (UTC-6:00 aka
        # Central Standard Time) is 12 a.m. on January 2nd in UTC
        local_dt = datetime(2024, 1, 1, 18, 0, tzinfo=ZoneInfo("America/Chicago"))
        utc_dt_next_day = dj_tz.localtime(local_dt, timezone=utc)
        assert utc_dt_next_day.date() != date(2024, 1, 1)
        assert utc_dt_next_day.date() == date(2024, 1, 2)
        assert dj_tz.localdate(utc_dt_next_day) == date(2024, 1, 1)

    def test_timezone_activation(self):
        """
        Django allows you to temporarily change the active timezone for the current thread.
        This is useful for setting the timezone to the user's timezone in middleware or another context.
        """
        assert dj_tz.get_current_timezone_name() == "America/Chicago"
        dj_tz.activate(ZoneInfo("America/New_York"))
        assert dj_tz.get_current_timezone_name() == "America/New_York"
        dj_tz.deactivate()  # Reset the active timezone
        assert dj_tz.get_current_timezone_name() == "America/Chicago"

    def test_timezone_override(self):
        """
        Django provides a context manager to temporarily override the active timezone.
        This is useful when you need to perform operations in a specific timezone.
        """
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

    def test_combine_date_and_time(self):
        """
        Combine a date object with a time object to create a datetime object. This is useful when you have separate
        date and time fields in a form and need to combine them into a single datetime object.

        **Note:** Django's SplitDateTimeField can be used for this purpose in forms.
        """
        datetime_obj = dj_tz.make_aware(
            datetime.combine(date(2024, 1, 1), time(22, 30))
        )
        assert datetime_obj.tzinfo == dj_tz.get_current_timezone()
