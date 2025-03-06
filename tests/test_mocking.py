"""
Tests for mocking datetime operations in Django.
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
        Test mocking the Django timezone.now() function.
        
        This is useful for testing code that depends on the current time,
        allowing you to control what "now" means in your tests.
        """
        mocked_now = datetime(2019, 1, 2, 0, 0, tzinfo=utc)
        mock_now.return_value = mocked_now
        django_now = dj_tz.now()

        assert django_now == mocked_now 