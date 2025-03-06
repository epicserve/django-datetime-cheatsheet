"""
Tests for datetime template rendering in Django.
"""
from datetime import datetime, timezone, timedelta
from zoneinfo import ZoneInfo

from django.template import Template, Context
from django.test import TestCase
from django.utils import timezone as dj_tz

from model_bakery import baker

utc = timezone.utc


class TestTemplateRendering(TestCase):
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

    def test_javascript_datetime_rendering(self):
        # Create a fixed datetime in UTC for demonstration purposes
        utc_dt = datetime(2024, 1, 2, 0, 0, tzinfo=utc)
        
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

    def test_timezone_template_tags(self):
        # Create a fixed datetime in UTC for demonstration purposes
        utc_dt = datetime(2024, 1, 2, 0, 0, tzinfo=utc)
        
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

    def test_model_display_methods(self):
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