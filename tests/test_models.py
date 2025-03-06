"""
Tests for datetime model operations in Django.
"""
import json
from datetime import datetime, timezone, timedelta
from zoneinfo import ZoneInfo

from django.core.serializers import serialize
from django.test import TestCase
from django.utils import timezone as dj_tz

from apps.events.models import Event

utc = timezone.utc


class TestModels(TestCase):
    def test_bulk_create_and_bulk_update(self):
        naive_start_time = datetime(2025, 2, 20, 16, 20)
        naive_end_time = naive_start_time + timedelta(hours=1)
        time_zones_to_test = [
            "America/Los_Angeles",
            "America/Denver",
            "America/Chicago",
            "America/New_York",
        ]

        events = []
        for time_zone in time_zones_to_test:
            tz_obj = ZoneInfo(time_zone)
            events.append(
                Event(
                    **{
                        "name": time_zone,
                        "start_time": dj_tz.make_aware(
                            naive_start_time, timezone=tz_obj
                        ),
                        "end_time": dj_tz.make_aware(naive_end_time, timezone=tz_obj),
                        "timezone": time_zone,
                    }
                )
            )

        Event.objects.bulk_create(events)

        # Assert that events are in the correct time UTC time according to their timezone
        serialized_events = [
            {"id": obj["pk"], **obj["fields"]}  # Flatten by merging pk and fields
            for obj in json.loads(serialize("json", Event.objects.all()))
        ]
        assert serialized_events == [
            {
                "end_time": "2025-02-21T01:20:00Z",
                "id": 1,
                "name": "America/Los_Angeles",
                "start_time": "2025-02-21T00:20:00Z",
                "timezone": "America/Los_Angeles",
            },
            {
                "end_time": "2025-02-21T00:20:00Z",
                "id": 2,
                "name": "America/Denver",
                "start_time": "2025-02-20T23:20:00Z",
                "timezone": "America/Denver",
            },
            {
                "end_time": "2025-02-20T23:20:00Z",
                "id": 3,
                "name": "America/Chicago",
                "start_time": "2025-02-20T22:20:00Z",
                "timezone": "America/Chicago",
            },
            {
                "end_time": "2025-02-20T22:20:00Z",
                "id": 4,
                "name": "America/New_York",
                "start_time": "2025-02-20T21:20:00Z",
                "timezone": "America/New_York",
            },
        ]

    def test_bulk_update(self):
        # First create the events
        naive_start_time = datetime(2025, 2, 20, 16, 20)
        naive_end_time = naive_start_time + timedelta(hours=1)
        time_zones_to_test = [
            "America/Los_Angeles",
            "America/Denver",
            "America/Chicago",
            "America/New_York",
        ]

        events = []
        for time_zone in time_zones_to_test:
            tz_obj = ZoneInfo(time_zone)
            events.append(
                Event(
                    **{
                        "name": time_zone,
                        "start_time": dj_tz.make_aware(
                            naive_start_time, timezone=tz_obj
                        ),
                        "end_time": dj_tz.make_aware(naive_end_time, timezone=tz_obj),
                        "timezone": time_zone,
                    }
                )
            )

        Event.objects.bulk_create(events)
        
        # Test bulk update by adding 1 hour to the start and end time
        events_to_update = []
        for event in Event.objects.all():
            event.start_time += timedelta(hours=1)
            event.end_time += timedelta(hours=1)
            events_to_update.append(event)

        Event.objects.bulk_update(events_to_update, ["start_time", "end_time"])

        # Assert that events have been updated by one hour and are in the correct time UTC time according to their timezone
        serialized_events = [
            {"id": obj["pk"], **obj["fields"]}  # Flatten by merging pk and fields
            for obj in json.loads(serialize("json", Event.objects.all()))
        ]
        assert serialized_events == [
            {
                "end_time": "2025-02-21T02:20:00Z",
                "id": 1,
                "name": "America/Los_Angeles",
                "start_time": "2025-02-21T01:20:00Z",
                "timezone": "America/Los_Angeles",
            },
            {
                "end_time": "2025-02-21T01:20:00Z",
                "id": 2,
                "name": "America/Denver",
                "start_time": "2025-02-21T00:20:00Z",
                "timezone": "America/Denver",
            },
            {
                "end_time": "2025-02-21T00:20:00Z",
                "id": 3,
                "name": "America/Chicago",
                "start_time": "2025-02-20T23:20:00Z",
                "timezone": "America/Chicago",
            },
            {
                "end_time": "2025-02-20T23:20:00Z",
                "id": 4,
                "name": "America/New_York",
                "start_time": "2025-02-20T22:20:00Z",
                "timezone": "America/New_York",
            },
        ] 