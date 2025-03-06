"""
Tests for datetime form operations in Django.
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
        assert 'value="2025-02-20 19:20:00"' in result

    def test_form_rendering_with_timezone_override(self):
        # Create a start and end time in a different timezone
        local_tz = ZoneInfo('America/Los_Angeles')
        start_time = datetime(2025, 2, 20, 16, 20, tzinfo=local_tz)

        # Create a form with a datetime field
        class EventForm(forms.ModelForm):
            class Meta:
                model = Event
                fields = "__all__"

        # Create an event with the start and end time in the local timezone.
        event = baker.make("events.Event", name='Event Test', timezone='America/Los_Angeles', start_time=start_time, end_time=start_time + timedelta(hours=1))

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

    def test_form_with_data(self):
        # Create a start and end time in a different timezone
        local_tz = ZoneInfo('America/Los_Angeles')
        start_time = datetime(2025, 2, 20, 16, 20, tzinfo=local_tz)

        # Create an event with the start and end time in the local timezone.
        event = baker.make("events.Event", name='Event Test', timezone='America/Los_Angeles', start_time=start_time, end_time=start_time + timedelta(hours=1))

        # Create a form with a datetime field
        class EventForm(forms.ModelForm):
            class Meta:
                model = Event
                fields = "__all__"

        # Test with data
        form = EventForm(instance=event, data={
            'name': 'Event Test',
            'start_time': '2025-02-20 16:20:00',
            'end_time': '2025-02-20 17:20:00',
            'timezone': 'America/Los_Angeles',
        })
        form.is_valid()
        form.initial['start_time'] = formats.localize_input((dj_tz.localtime(event.start_time, local_tz)))
        form.initial['end_time'] = formats.localize_input((dj_tz.localtime(event.end_time, local_tz)))
        result = self.render_str_template('{{ form }}', {'form': form})

        # Assert that the initial value is in the local timezone of the event.
        assert 'value="2025-02-20 16:20:00"' in result
        assert 'value="2025-02-20 17:20:00"' in result

    def test_form_field_rendering(self):
        # Create a start and end time in a different timezone
        local_tz = ZoneInfo('America/Los_Angeles')
        start_time = datetime(2025, 2, 20, 16, 20, tzinfo=local_tz)

        # Create an event with the start and end time in the local timezone.
        event = baker.make("events.Event", name='Event Test', timezone='America/Los_Angeles', start_time=start_time, end_time=start_time + timedelta(hours=1))

        # Create a form with a datetime field
        class EventForm(forms.ModelForm):
            class Meta:
                model = Event
                fields = "__all__"

        # Test with rendering a field
        form = EventForm(instance=event, data={
            'name': 'Event Test',
            'start_time': '2025-02-20 16:20:00',
            'end_time': '2025-02-20 17:20:00',
            'timezone': 'America/Los_Angeles',
        })
        form.is_valid()
        form.initial['start_time'] = formats.localize_input((dj_tz.localtime(event.start_time, local_tz)))
        form.initial['end_time'] = formats.localize_input((dj_tz.localtime(event.end_time, local_tz)))
        start_field_result = self.render_str_template('{{ form.start_time }}', {'form': form})
        end_field_result = self.render_str_template('{{ form.end_time }}', {'form': form})

        # Assert that the initial value is in the local timezone of the event.
        assert 'value="2025-02-20 16:20:00"' in start_field_result
        assert 'value="2025-02-20 17:20:00"' in end_field_result 