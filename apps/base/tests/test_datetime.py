import json
from datetime import date, datetime, time, timezone, timedelta
from unittest.mock import patch
from zoneinfo import ZoneInfo

from django import forms
from django.conf import settings
from django.core.serializers import serialize
from django.template import Template, Context
from django.test import TestCase
from django.utils import timezone as dj_tz, formats
from model_bakery import baker

from apps.events.models import Event

utc = timezone.utc


class TestDateTime(TestCase):
    def test_datetime(self):
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

        # Test overriding the timezone with in a ModeForm
        class EventForm(forms.ModelForm):
            class Meta:
                model = Event
                fields = "__all__"

            def is_valid(self):
                with dj_tz.override(ZoneInfo(self.data["timezone"])):
                    return super().is_valid()

        data = {
            "name": event.name,
            "start_time": formats.date_format(event_start_time, "m/d/Y H:i:s"),
            "end_time": formats.date_format(event_end_time, "m/d/Y H:i:s"),
            "timezone": "America/New_York",
        }
        form = EventForm(instance=event, data=data)
        assert form.is_valid() is True
        form.save()
        event.refresh_from_db()
        assert dj_tz.localtime(
            event.start_time, ZoneInfo("America/New_York")
        ) == event_start_time.replace(tzinfo=ZoneInfo("America/New_York"))

        """
        Combine a date object with a time object to create a datetime object

        It should be noted that you can use Django's SplitDateTimeField if you want to combine a date and time in a
        form that is using separate fields.
        """
        datetime_obj = dj_tz.make_aware(
            datetime.combine(date(2024, 1, 1), time(22, 30))
        )
        assert datetime_obj.tzinfo == dj_tz.get_current_timezone()

    def test_formating_datetime(self):
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

        """
        Since `date_format()` doesn't automatically convert datetimes in UTC to the current timezone, it's best to
        create some shortcut functions to do this for you.
        """

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

        # Or create even shorter functions
        def local_short_datetime_format(dt):
            return formats.date_format(
                dj_tz.localtime(dt), settings.SHORT_DATETIME_FORMAT
            )

        assert local_short_datetime_format(utc_dt) == "10/01/2024 8:30 a.m."

    @staticmethod
    def render_str_template(template_str, context):
        template = Template(template_str)
        context = Context(context)
        return template.render(context).strip()

    def test_formatting_datetimes_in_a_django_template(self):
        # Create a fixed datetime in UTC for demonstration purposes and a UTC that as a different day than localtime
        utc_dt = datetime(2024, 1, 2, 0, 0, tzinfo=utc)

        # Render a datetime object using Django's default formatting for Django templates which is
        # the `settings.DATETIME_FORMAT`.
        result = self.render_str_template("{{ utc_dt }}", {"utc_dt": utc_dt})
        assert result == "Jan. 1, 2024, 6 p.m."

        """
        Render a datetime object using Django's date filter

        Ref: https://docs.djangoproject.com/en/4.0/ref/templates/builtins/#date

        Notice that when using the `date` filter the day is in the local timezone day because the rendered day is the
        1st and not the 2nd
        """

        # Render a datetime object using the default DATE_FORMAT setting
        result = self.render_str_template("{{ utc_dt|date }}", {"utc_dt": utc_dt})
        assert result == "Jan. 1, 2024"

        # Render a date using the SHORT_DATE_FORMAT setting
        result = self.render_str_template(
            "{{ utc_dt|date:'SHORT_DATE_FORMAT' }}", {"utc_dt": utc_dt}
        )
        assert result == "01/01/2024"

        # Render a date using a custom setting
        result = self.render_str_template(
            "{{ utc_dt|date:'F j, Y' }}", {"utc_dt": utc_dt}
        )
        assert result == "January 1, 2024"

        # Render a date using the SHORT_DATETIME_FORMAT setting
        result = self.render_str_template(
            "{{ utc_dt|date:'SHORT_DATETIME_FORMAT' }}", {"utc_dt": utc_dt}
        )
        assert result == "01/01/2024 6 p.m."

        # Render a datetime object in order to pass it into Javascript
        result = self.render_str_template(
            """
            <script>
              // Parse Django's formatted date
              const datetime = new Date('{{ utc_dt|date:'c' }}');
              console.log('Django filtered datetime:', datetime);
            </script>
            """,
            {"utc_dt": utc_dt},
        )
        assert "new Date('2024-01-01T18:00:00-06:00')" in result

        # Render a datetime object that has a different timezone than the active timezone
        pt_dt = dj_tz.localtime(utc_dt, ZoneInfo("America/Los_Angeles"))
        assert pt_dt.strftime("%Y-%m-%d %-I:%M %p") == "2024-01-01 4:00 PM"
        assert dj_tz.get_current_timezone_name() == "America/Chicago"
        result = self.render_str_template("{{ pt_dt }}", {"pt_dt": pt_dt})
        assert "Jan. 1, 2024, 6 p.m." in result

        # Render a datetime object in a different timezone using the timezone template tag
        result = self.render_str_template(
            '{% load tz %}{% timezone "America/Los_Angeles" %}{{ pt_dt }}{% endtimezone %}',
            {"pt_dt": pt_dt},
        )
        assert "Jan. 1, 2024, 4 p.m." in result

        # Render a datetime object in a different timezone using the localtime template tag.

        p_dt = datetime(2024, 1, 1, 13, 30, tzinfo=ZoneInfo("America/Los_Angeles"))
        event = baker.make(
            "events.event",
            start_time=p_dt,
            end_time=p_dt + timedelta(hours=1),
            timezone="America/Los_Angeles",
        )
        event.refresh_from_db()
        assert event.start_time.tzinfo == utc
        assert p_dt.tzinfo == ZoneInfo("America/Los_Angeles")

        result = self.render_str_template(
            "{{ event.display_start_time }}", {"event": event}
        )
        assert "Jan. 1, 2024, 1:30 p.m." in result

    @patch("django.utils.timezone.now")
    def test_mocking_datetime(self, mock_now):
        mocked_now = datetime(2019, 1, 2, 0, 0, tzinfo=utc)
        mock_now.return_value = mocked_now
        django_now = dj_tz.now()

        assert django_now == mocked_now

    def test_form_rendering(self):

        # The Django apps current timezone
        assert 'America/Chicago' == dj_tz.get_current_timezone_name()

        # Create a start and end time in a different timezone. Let's use 4:20 PM because it's funny and because in PST
        # it will be the next day in UTC which is a good test case.
        local_tz = ZoneInfo('America/Los_Angeles')
        start_time = datetime(2025, 2, 20, 16, 20, tzinfo=local_tz)

        # Create a form with a datetime field
        class EventForm(forms.ModelForm):
            class Meta:
                model = Event
                fields = "__all__"

        # Create an event with the start and end time in the local timezone.
        event = baker.make("events.Event", name='Event Test', timezone='America/Los_Angeles', start_time=start_time, end_time=start_time + timedelta(hours=1))

        # Assert that the event is converted to UTC correctly
        assert event.start_time == datetime(2025, 2, 21, 0, 20, tzinfo=utc)
        assert event.end_time == datetime(2025, 2, 21, 1, 20, tzinfo=utc)

        # Initialize a form with the event
        form = EventForm(instance=event)

        # Render the form
        result = self.render_str_template('{{ form }}', {'form': form})

        # The following shows that the initial value is in the local timezone using Django's current timezone which is
        # America/Chicago which isn't what we want.
        assert 'value="2025-02-20 18:20:00"' in result
        assert 'value="2025-02-20 18:20:00"' in result

        # Render the initial start and end time values using the event's timezone by using a form that overrides the
        # initial value.
        form = EventForm(instance=event)

        # Override the initial value and render to a string to make sure the time isn't converted to local time by using
        # Django's current timezone. Use the same function `formats.localize_input()` render to a string that
        # django.forms.widgets.DateTimeInput widget uses to render the initial value.
        form.initial['start_time'] = formats.localize_input((dj_tz.localtime(event.start_time, local_tz)))
        form.initial['end_time'] = formats.localize_input((dj_tz.localtime(event.end_time, local_tz)))
        result = self.render_str_template('{{ form }}', {'form': form})

        # Assert that the initial value is in the local timezone of the event.
        assert 'value="2025-02-20 16:20:00"' in result
        assert 'value="2025-02-20 17:20:00"' in result

        # Test with data
        form = EventForm(instance=event, data={
            'name': 'Event Test',
            'start_time': '2025-02-20 16:20:00',
            'end_time': '2025-02-20 17:20:00',
        })
        form.is_valid()
        form.initial['start_time'] = formats.localize_input((dj_tz.localtime(event.start_time, local_tz)))
        form.initial['end_time'] = formats.localize_input((dj_tz.localtime(event.end_time, local_tz)))
        result = self.render_str_template('{{ form }}', {'form': form})

        # Assert that the initial value is in the local timezone of the event.
        assert 'value="2025-02-20 16:20:00"' in result
        assert 'value="2025-02-20 17:20:00"' in result

        # Test with rendering a field
        # Test with data
        form = EventForm(instance=event, data={
            'name': 'Event Test',
            'start_time': '2025-02-20 16:20:00',
            'end_time': '2025-02-20 17:20:00',
        })
        form.is_valid()
        form.initial['start_time'] = formats.localize_input((dj_tz.localtime(event.start_time, local_tz)))
        form.initial['end_time'] = formats.localize_input((dj_tz.localtime(event.end_time, local_tz)))
        start_field_result = self.render_str_template('{{ form.start_time }}', {'form': form})
        end_field_result = self.render_str_template('{{ form.end_time }}', {'form': form})

        # Assert that the initial value is in the local timezone of the event.
        assert 'value="2025-02-20 16:20:00"' in start_field_result
        assert 'value="2025-02-20 17:20:00"' in end_field_result


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
