"""
Formatting datetime objects in Django
"""

from datetime import datetime, timezone

from django.conf import settings
from django.test import TestCase
from django.utils import timezone as dj_tz, formats

utc = timezone.utc


class TestDateTimeFormatting(TestCase):
    def test_datetime_string_formats(self):
        """
        Django provides several ways to format datetime objects into strings.
        The `formats.date_format()` function is the most common way to format datetimes.

        **Note:** The format function **DOESN'T** automatically convert datetime objects
        that are in UTC to the current timezone.
        """
        # Create a fixed datetime in UTC for demonstration purposes
        utc_dt = datetime(2024, 10, 1, 13, 30, tzinfo=utc)

        assert (
            formats.date_format(utc_dt, settings.DATETIME_FORMAT)
            == "Oct. 1, 2024, 1:30 p.m."
        )
        assert (
            formats.date_format(utc_dt, settings.SHORT_DATETIME_FORMAT)
            == "10/01/2024 1:30 p.m."
        )
        assert formats.date_format(utc_dt, settings.SHORT_DATE_FORMAT) == "10/01/2024"
        assert formats.date_format(utc_dt, "Y-m-d") == "2024-10-01"

    def test_local_datetime_format(self):
        """
        Since `date_format()` doesn't automatically convert times in UTC to the current timezone,
        it's best to create a shortcut function to do this for you. Then you can use this function
        to format datetimes in the current timezone.
        """

        def local_datetime_format(dt, df=settings.DATETIME_FORMAT):
            return formats.date_format(dj_tz.localtime(dt), df)

        # Create a fixed datetime in UTC for demonstration purposes
        utc_dt = datetime(2024, 10, 1, 13, 30, tzinfo=utc)

        assert local_datetime_format(utc_dt) == "Oct. 1, 2024, 8:30 a.m."
        assert (
            local_datetime_format(utc_dt, settings.DATETIME_FORMAT)
            == "Oct. 1, 2024, 8:30 a.m."
        )

        assert (
            local_datetime_format(utc_dt, settings.SHORT_DATETIME_FORMAT)
            == "10/01/2024 8:30 a.m."
        )

    def test_datetime_format_helper_functions(self):
        """
        For common formatting needs, you can create even more specialized helper functions. For example, if you need to
        format a datetime object into the `SHORT_DATETIME_FORMAT` string in the local timezone, you can create a
        helper function like the following.

        Then everywhere you need to format a datetime in the `SHORT_DATETIME_FORMAT` string in the local timezone, you
        can call this function.
        """
        # Create a fixed datetime in UTC for demonstration purposes
        utc_dt = datetime(2024, 10, 1, 13, 30, tzinfo=utc)

        # Create even shorter functions
        def local_short_datetime_format(dt):
            return formats.date_format(
                dj_tz.localtime(dt), settings.SHORT_DATETIME_FORMAT
            )

        assert local_short_datetime_format(utc_dt) == "10/01/2024 8:30 a.m."
