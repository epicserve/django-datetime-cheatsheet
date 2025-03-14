"""
Working with datetime fields in forms
"""

from datetime import datetime, timezone, timedelta
from zoneinfo import ZoneInfo

from django import forms
from django.template import Template, Context
from django.test import TestCase
from django.utils import timezone as dj_tz, formats

from apps.events.models import Event
from model_bakery import baker

utc = timezone.utc


class TestForms(TestCase):
    @staticmethod
    def render_str_template(template_str, context):
        template = Template(template_str)
        context = Context(context)
        return template.render(context).strip()

    def test_timezone_override_in_form(self):
        """
        When working with forms that handle datetime fields, it's often necessary
        to consider the timezone of the input data. By overriding the `is_valid` method,
        you can ensure that the form validates the data in the correct timezone.
        """
        # Use override to temporarily save a model's datetime in a different timezone
        with dj_tz.override(ZoneInfo("America/Los_Angeles")):
            event_start_time = dj_tz.make_aware(datetime(2024, 1, 1, 22, 30))
            event_end_time = event_start_time + timedelta(hours=1)
            event = baker.make("events.Event")
            event.start_time = event_start_time
            event.end_time = event_end_time
            event.save()

        # Test overriding the timezone with in a ModelForm
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

    def test_form_rendering(self):
        """
        By default, Django renders datetime fields in the current timezone,
        which may not be what you want if your model stores the timezone for each database table record. For example,
        if we create a model form using the Event model in this project, we want to make sure that the start and end
        times get rendered in the timezone specified by the model's timezone field.
        """
        # The Django apps current timezone
        assert "America/Chicago" == dj_tz.get_current_timezone_name()

        # Create a start and end time in a different timezone. Let's use 5:00 PM in PST because it will be the next day
        # in UTC which is a good test case.
        local_tz = ZoneInfo("America/Los_Angeles")
        start_time = datetime(2025, 2, 20, 17, 00, tzinfo=local_tz)

        # Create a form with a datetime field
        class EventForm(forms.ModelForm):
            class Meta:
                model = Event
                fields = "__all__"

        # Create an event with the start and end time in the local timezone.
        event = baker.make(
            "events.Event",
            name="Event Test",
            timezone="America/Los_Angeles",
            start_time=start_time,
            end_time=start_time + timedelta(hours=1),
        )
        event.refresh_from_db()

        # Assert that the event is converted to UTC correctly
        assert event.start_time == datetime(2025, 2, 21, 1, 0, tzinfo=utc)
        assert event.end_time == datetime(2025, 2, 21, 2, 0, tzinfo=utc)

        # Initialize a form with the event
        form = EventForm(instance=event)

        # Render the form
        result = self.render_str_template("{{ form }}", {"form": form})

        # The following shows that the initial value is in the local timezone using Django's current timezone which is
        # America/Chicago which **ISN'T** what we want.
        assert 'value="2025-02-20 19:00:00"' in result
        assert 'value="2025-02-20 20:00:00"' in result

        # Instead if you want to render the datetime fields in the model's timezone, you can override the initial values
        # in the form.

        # Create a form with a datetime field
        class LocalEventTimeForm(forms.ModelForm):
            class Meta:
                model = Event
                fields = "__all__"

            def __init__(self, *args, **kwargs):
                super().__init__(*args, **kwargs)
                if self.instance is not None:
                    self.initial["start_time"] = formats.localize_input(
                        dj_tz.localtime(
                            event.start_time, ZoneInfo(self.instance.timezone)
                        )
                    )
                    self.initial["end_time"] = formats.localize_input(
                        dj_tz.localtime(
                            event.end_time, ZoneInfo(self.instance.timezone)
                        )
                    )

        # Initialize a form with the event
        form = LocalEventTimeForm(instance=event)

        # Render the form
        result = self.render_str_template("{{ form }}", {"form": form})

        # The following shows that the initial values for the start and end are now correctly rendered in the timezone
        # for the event's timezone.
        assert 'value="2025-02-20 17:00:00"' in result
        assert 'value="2025-02-20 18:00:00"' in result

        # Also test rendering individual fields
        start_time_result = self.render_str_template(
            "{{ form.start_time }}", {"form": form}
        )
        end_time_result = self.render_str_template(
            "{{ form.end_time }}", {"form": form}
        )

        assert 'value="2025-02-20 17:00:00"' in start_time_result
        assert 'value="2025-02-20 18:00:00"' in end_time_result

        # Now make sure the form also renders the timezone field correctly when data is sumbitted.
        form = LocalEventTimeForm(
            instance=event,
            data={
                "name": "Event Test",
                "start_time": "2025-02-20 19:00:00",
                "end_time": "2025-02-20 20:00:00",
                "timezone": "America/Los_Angeles",
            },
        )
        form.is_valid()
        result = self.render_str_template("{{ form }}", {"form": form})

        # Assert that the initial value is in the local timezone of the event.
        assert 'value="2025-02-20 19:00:00"' in result
        assert 'value="2025-02-20 20:00:00"' in result
