"""
Tests for datetime formatting operations in Django.
"""
from datetime import datetime, timezone

from django.conf import settings
from django.test import TestCase
from django.utils import timezone as dj_tz, formats

utc = timezone.utc


class TestDateTimeFormatting(TestCase):
    def test_formatting_datetime(self):
        # Create a fixed datetime in UTC for demonstration purposes
        utc_dt = datetime(2024, 10, 1, 13, 30, tzinfo=utc)

        """
        Format a datetime as a string

        **NOTE:** The format function DOESN'T automatically convert datetime objects that are in UTC to the current timezone.
        """
        assert (
            formats.date_format(utc_dt, settings.DATETIME_FORMAT)
            == "Oct. 1, 2024, 1:30 p.m."
        )
        assert (
            formats.date_format(utc_dt, settings.SHORT_DATETIME_FORMAT)
            == "10/01/2024 1:30 p.m."
        )
        assert formats.date_format(utc_dt, settings.SHORT_DATE_FORMAT) == "10/01/2024"

    def test_local_datetime_format(self):
        """
        Since `date_format()` doesn't automatically convert datetimes in UTC to the current timezone, it's best to
        create some shortcut functions to do this for you.
        """
        # Create a fixed datetime in UTC for demonstration purposes
        utc_dt = datetime(2024, 10, 1, 13, 30, tzinfo=utc)

        def local_datetime_format(dt, df=settings.DATETIME_FORMAT):
            return formats.date_format(dj_tz.localtime(dt), df)

        assert local_datetime_format(utc_dt) == "Oct. 1, 2024, 8:30 a.m."
        assert (
            local_datetime_format(utc_dt, settings.DATETIME_FORMAT)
            == "Oct. 1, 2024, 8:30 a.m."
        )

        assert (
            local_datetime_format(utc_dt, settings.SHORT_DATETIME_FORMAT)
            == "10/01/2024 8:30 a.m."
        )

    def test_local_short_datetime_format(self):
        # Create a fixed datetime in UTC for demonstration purposes
        utc_dt = datetime(2024, 10, 1, 13, 30, tzinfo=utc)

        # Create even shorter functions
        def local_short_datetime_format(dt):
            return formats.date_format(
                dj_tz.localtime(dt), settings.SHORT_DATETIME_FORMAT
            )

        assert local_short_datetime_format(utc_dt) == "10/01/2024 8:30 a.m." 