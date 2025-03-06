"""
Mocking datetime operations in Django Tests
"""

from datetime import datetime, timezone
from unittest.mock import patch

from django.test import TestCase
from django.utils import timezone as dj_tz

utc = timezone.utc


class TestMocking(TestCase):
    @patch("django.utils.timezone.now")
    def test_mocking_datetime(self, mock_now):
        """
        When testing code that depends on the current time, it's often necessary to mock the datetime to ensure
        consistent test results. This is especially important for tests that might behave differently depending on the
        time of day or day of the week.

        Django's `timezone.now()` function is commonly used to get the current time, so mocking it allows you to
        control what "now" means in your tests.

        For example, if you use the decorator `@patch("django.utils.timezone.now")` on a test method and pass in
        `mock_now` as an argument, you can then set the return value of `mock_now` to a fixed datetime object.

        See the test `tests.test_mocking.TestMocking.test_mocking_datetime` for the full example.
        """
        mocked_now = datetime(2019, 1, 2, 0, 0, tzinfo=utc)
        mock_now.return_value = mocked_now
        django_now = dj_tz.now()

        assert django_now == mocked_now
