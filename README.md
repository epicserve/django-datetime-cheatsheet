# Django Datetime Cheat Sheet

When working with datetime objects in Django there seems to be a lot of confusion around timezones, formatting, and
conversions. This cheatsheet aims to provide a quick reference for common datetime operations in Django, including
timezone handling, formatting, and testing.

This guide assumes you're familiar with Django and Python's datetime module, and that you have `settings.USE_TZ` set to
`True` in your Django project. Also, for this guide, we'll assume the `TIME_ZONE` setting in your Django project is
set `'America/Chicago'`.

This cheatsheet is also a Django project that you can run locally to see how the code examples work in practice. Please
use this repository as a way to play around with the code examples provided in the blog post. To get started, 
clone this repository and make sure you have [UV][uv] and [Just][just] installed. Then run the following Just command:

```bash
just run_initial_setup
```

Once the setup is complete, you can run the tests that were used to create the majority of the code in the Cheat Sheet.

```bash
just test
```

You can also follow along with the cheat sheet by starting a Django shell:

```bash
uv run ./manage.py shell
```

<!-- section-examples-start -->
## Basic datetime operations in Django

Basic operations with datetime objects in Django, including timezone handling and conversions.

### Datetime Basics

The following code demonstrates how to work with timezone-aware and naive datetime objects, how to get the
current time in different timezones, and how to convert between timezones. `settings.TIME_ZONE` is set to
`"America/Chicago"` in the Django settings and `utc` equals `datetime.timezone.utc`.

<div align="right" style="margin-bottom: -10px;"><a href="https://github.com/epicserve/django-datetime-cheatsheet/tree/wip/tests/test_datetime_basics.py#L20-L66" title="View full example in source code" style="font-size: 0.8em; color: #5a5a5a; text-decoration: none;">📝 View full example</a></div>

```python
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
mountain_datetime = dj_tz.localtime(local_dt, timezone=ZoneInfo("America/Denver"))
assert mountain_datetime.tzinfo == ZoneInfo("America/Denver")

# Avoid bugs with dates by using Django's localdate function
# 6 p.m. on January 1st in the local timezone is 12 a.m. on January 2nd in UTC
local_dt = datetime(2024, 1, 1, 18, 0, tzinfo=ZoneInfo("America/Chicago"))
utc_dt_next_day = dj_tz.localtime(local_dt, timezone=utc)
assert utc_dt_next_day.date() != date(2024, 1, 1)
assert utc_dt_next_day.date() == date(2024, 1, 2)
assert dj_tz.localdate(utc_dt_next_day) == date(2024, 1, 1)
```

### Timezone Activation

Django allows you to temporarily change the active timezone for the current thread.
This is useful for setting the timezone to the user's timezone in middleware or another context.

<div align="right" style="margin-bottom: -10px;"><a href="https://github.com/epicserve/django-datetime-cheatsheet/tree/wip/tests/test_datetime_basics.py#L68-L77" title="View full example in source code" style="font-size: 0.8em; color: #5a5a5a; text-decoration: none;">📝 View full example</a></div>

```python
assert dj_tz.get_current_timezone_name() == "America/Chicago"
dj_tz.activate(ZoneInfo("America/New_York"))
assert dj_tz.get_current_timezone_name() == "America/New_York"
dj_tz.deactivate()  # Reset the active timezone
assert dj_tz.get_current_timezone_name() == "America/Chicago"
```

### Timezone Override

Django provides a context manager to temporarily override the active timezone.
This is useful when you need to perform operations in a specific timezone.

<div align="right" style="margin-bottom: -10px;"><a href="https://github.com/epicserve/django-datetime-cheatsheet/tree/wip/tests/test_datetime_basics.py#L79-L97" title="View full example in source code" style="font-size: 0.8em; color: #5a5a5a; text-decoration: none;">📝 View full example</a></div>

```python
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
```

### Combine Date And Time

Combine a date object with a time object to create a datetime object. This is useful when you have separate
date and time fields in a form and need to combine them into a single datetime object.

**Note:** Django's SplitDateTimeField can be used for this purpose in forms.

<div align="right" style="margin-bottom: -10px;"><a href="https://github.com/epicserve/django-datetime-cheatsheet/tree/wip/tests/test_datetime_basics.py#L99-L109" title="View full example in source code" style="font-size: 0.8em; color: #5a5a5a; text-decoration: none;">📝 View full example</a></div>

```python
datetime_obj = dj_tz.make_aware(datetime.combine(date(2024, 1, 1), time(22, 30)))
assert datetime_obj.tzinfo == dj_tz.get_current_timezone()
```

## Formatting datetime objects in Django



### Datetime String Formats

Django provides several ways to format datetime objects into strings.
The `formats.date_format()` function is the most common way to format datetimes.

**Note:** The format function **DOESN'T** automatically convert datetime objects
that are in UTC to the current timezone.

<div align="right" style="margin-bottom: -10px;"><a href="https://github.com/epicserve/django-datetime-cheatsheet/tree/wip/tests/test_datetime_formatting.py#L15-L35" title="View full example in source code" style="font-size: 0.8em; color: #5a5a5a; text-decoration: none;">📝 View full example</a></div>

```python
# Create a fixed datetime in UTC for demonstration purposes
utc_dt = datetime(2024, 10, 1, 13, 30, tzinfo=utc)

assert (
    formats.date_format(utc_dt, settings.DATETIME_FORMAT) == "Oct. 1, 2024, 1:30 p.m."
)
assert (
    formats.date_format(utc_dt, settings.SHORT_DATETIME_FORMAT)
    == "10/01/2024 1:30 p.m."
)
assert formats.date_format(utc_dt, settings.SHORT_DATE_FORMAT) == "10/01/2024"
assert formats.date_format(utc_dt, "Y-m-d") == "2024-10-01"
```

### Local Datetime Format

Since `date_format()` doesn't automatically convert times in UTC to the current timezone,
it's best to create a shortcut function to do this for you. Then you can use this function
to format datetimes in the current timezone.

<div align="right" style="margin-bottom: -10px;"><a href="https://github.com/epicserve/django-datetime-cheatsheet/tree/wip/tests/test_datetime_formatting.py#L37-L59" title="View full example in source code" style="font-size: 0.8em; color: #5a5a5a; text-decoration: none;">📝 View full example</a></div>

```python
def local_datetime_format(dt, df=settings.DATETIME_FORMAT):
    return formats.date_format(dj_tz.localtime(dt), df)


# Create a fixed datetime in UTC for demonstration purposes
utc_dt = datetime(2024, 10, 1, 13, 30, tzinfo=utc)

assert local_datetime_format(utc_dt) == "Oct. 1, 2024, 8:30 a.m."
assert (
    local_datetime_format(utc_dt, settings.DATETIME_FORMAT) == "Oct. 1, 2024, 8:30 a.m."
)

assert (
    local_datetime_format(utc_dt, settings.SHORT_DATETIME_FORMAT)
    == "10/01/2024 8:30 a.m."
)
```

### Datetime Format Helper Functions

For common formatting needs, you can create even more specialized helper functions. For example, if you need to
format a datetime object into the `SHORT_DATETIME_FORMAT` string in the local timezone, you can create a
helper function like the following.

Then everywhere you need to format a datetime in the `SHORT_DATETIME_FORMAT` string in the local timezone, you
can call this function.

<div align="right" style="margin-bottom: -10px;"><a href="https://github.com/epicserve/django-datetime-cheatsheet/tree/wip/tests/test_datetime_formatting.py#L61-L79" title="View full example in source code" style="font-size: 0.8em; color: #5a5a5a; text-decoration: none;">📝 View full example</a></div>

```python
# Create a fixed datetime in UTC for demonstration purposes
utc_dt = datetime(2024, 10, 1, 13, 30, tzinfo=utc)


# Create even shorter functions
def local_short_datetime_format(dt):
    return formats.date_format(dj_tz.localtime(dt), settings.SHORT_DATETIME_FORMAT)


assert local_short_datetime_format(utc_dt) == "10/01/2024 8:30 a.m."
```

## Working with datetime fields in forms



### Timezone Override In Form

When working with forms that handle datetime fields, it's often necessary
to consider the timezone of the input data. By overriding the `is_valid` method,
you can ensure that the form validates the data in the correct timezone.

<div align="right" style="margin-bottom: -10px;"><a href="https://github.com/epicserve/django-datetime-cheatsheet/tree/wip/tests/test_forms.py#L26-L63" title="View full example in source code" style="font-size: 0.8em; color: #5a5a5a; text-decoration: none;">📝 View full example</a></div>

```python
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
```

### Form Rendering

By default, Django renders datetime fields in the current timezone,
which may not be what you want if your model stores the timezone for each database table record. For example,
if we create a model form using the Event model in this project, we want to make sure that the start and end
times get rendered in the timezone specified by the model's timezone field.

<div align="right" style="margin-bottom: -10px;"><a href="https://github.com/epicserve/django-datetime-cheatsheet/tree/wip/tests/test_forms.py#L65-L171" title="View full example in source code" style="font-size: 0.8em; color: #5a5a5a; text-decoration: none;">📝 View full example</a></div>

```python
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
result = render_template("{{ form }}", {"form": form})

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
                dj_tz.localtime(event.start_time, ZoneInfo(self.instance.timezone))
            )
            self.initial["end_time"] = formats.localize_input(
                dj_tz.localtime(event.end_time, ZoneInfo(self.instance.timezone))
            )


# Initialize a form with the event
form = LocalEventTimeForm(instance=event)

# Render the form
result = render_template("{{ form }}", {"form": form})

# The following shows that the initial values for the start and end are now correctly rendered in the timezone
# for the event's timezone.
assert 'value="2025-02-20 17:00:00"' in result
assert 'value="2025-02-20 18:00:00"' in result

# Also test rendering individual fields
start_time_result = self.render_str_template("{{ form.start_time }}", {"form": form})
end_time_result = self.render_str_template("{{ form.end_time }}", {"form": form})

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
result = render_template("{{ form }}", {"form": form})

# Assert that the initial value is in the local timezone of the event.
assert 'value="2025-02-20 19:00:00"' in result
assert 'value="2025-02-20 20:00:00"' in result
```

## Mocking datetime operations in Django Tests



### Mocking Datetime

When testing code that depends on the current time, it's often necessary to mock the datetime to ensure
consistent test results. This is especially important for tests that might behave differently depending on the
time of day or day of the week.

Django's `timezone.now()` function is commonly used to get the current time, so mocking it allows you to
control what "now" means in your tests.

For example, if you use the decorator `@patch("django.utils.timezone.now")` on a test method and pass in
`mock_now` as an argument, you can then set the return value of `mock_now` to a fixed datetime object.

See the test `tests.test_mocking.TestMocking.test_mocking_datetime` for the full example.

<div align="right" style="margin-bottom: -10px;"><a href="https://github.com/epicserve/django-datetime-cheatsheet/tree/wip/tests/test_mocking.py#L16-L34" title="View full example in source code" style="font-size: 0.8em; color: #5a5a5a; text-decoration: none;">📝 View full example</a></div>

```python
mocked_now = datetime(2019, 1, 2, 0, 0, tzinfo=utc)
mock_now.return_value = mocked_now
django_now = dj_tz.now()

assert django_now == mocked_now
```

## Working with Date Times in Models



### Bulk Create And Bulk Update

When creating multiple model instances with datetime fields in bulk,
it's important to ensure that the datetimes are stored correctly in the database.
This test demonstrates how to create events in different timezones using bulk_create.

<div align="right" style="margin-bottom: -10px;"><a href="https://github.com/epicserve/django-datetime-cheatsheet/tree/wip/tests/test_models.py#L19-L86" title="View full example in source code" style="font-size: 0.8em; color: #5a5a5a; text-decoration: none;">📝 View full example</a></div>

```python
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
                "start_time": dj_tz.make_aware(naive_start_time, timezone=tz_obj),
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
```

### Bulk Update

Handle datetime fields in bulk update operations.

When updating multiple model instances with datetime fields in bulk,
it's important to ensure that the datetimes are updated correctly in the database.
This test demonstrates how to update events in different timezones using bulk_update.

<div align="right" style="margin-bottom: -10px;"><a href="https://github.com/epicserve/django-datetime-cheatsheet/tree/wip/tests/test_models.py#L88-L167" title="View full example in source code" style="font-size: 0.8em; color: #5a5a5a; text-decoration: none;">📝 View full example</a></div>

```python
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
                "start_time": dj_tz.make_aware(naive_start_time, timezone=tz_obj),
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
```

## Datetime Template rendering in Django



### Formatting Datetimes In A Django Template

Django templates automatically handle timezone conversion when rendering datetime objects.
The default format is determined by the DATETIME_FORMAT setting.

The `date` filter can be used to format datetime objects in different ways.

<div align="right" style="margin-bottom: -10px;"><a href="https://github.com/epicserve/django-datetime-cheatsheet/tree/wip/tests/test_templates.py#L24-L62" title="View full example in source code" style="font-size: 0.8em; color: #5a5a5a; text-decoration: none;">📝 View full example</a></div>

```python
# Create a fixed datetime in UTC for demonstration purposes and a UTC that as a different day than localtime
utc_dt = datetime(2024, 1, 2, 0, 0, tzinfo=utc)

# Render a datetime object using Django's default formatting for Django templates which is
# the `settings.DATETIME_FORMAT`.
result = render_template("{{ utc_dt }}", {"utc_dt": utc_dt})
assert result == "Jan. 1, 2024, 6 p.m."

# Render a datetime object using Django's date filter. The date filter uses whatever format
# `settings.DATE_FORMAT` is set to. Also, notice that when using the `date` filter the day is in the local
# timezone day because the rendered day is the 1st and not the 2nd
# Ref: https://docs.djangoproject.com/en/4.0/ref/templates/builtins/#date
result = render_template("{{ utc_dt|date }}", {"utc_dt": utc_dt})
assert result == "Jan. 1, 2024"

# Render a date using the SHORT_DATE_FORMAT setting
result = self.render_str_template(
    "{{ utc_dt|date:'SHORT_DATE_FORMAT' }}", {"utc_dt": utc_dt}
)
assert result == "01/01/2024"

# Render a date using a custom setting
result = self.render_str_template("{{ utc_dt|date:'F j, Y' }}", {"utc_dt": utc_dt})
assert result == "January 1, 2024"

# Render a date using the SHORT_DATETIME_FORMAT setting
result = self.render_str_template(
    "{{ utc_dt|date:'SHORT_DATETIME_FORMAT' }}", {"utc_dt": utc_dt}
)
assert result == "01/01/2024 6 p.m."
```

### Javascript Datetime Rendering

When passing datetime objects to JavaScript, it's important to format them
in a way that JavaScript can understand. The 'c' format specifier outputs
an ISO 8601 formatted date, which is ideal for JavaScript.

<div align="right" style="margin-bottom: -10px;"><a href="https://github.com/epicserve/django-datetime-cheatsheet/tree/wip/tests/test_templates.py#L64-L84" title="View full example in source code" style="font-size: 0.8em; color: #5a5a5a; text-decoration: none;">📝 View full example</a></div>

```python
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
```

### Timezone Template Tags

Use timezone template tags to control datetime rendering.

Django provides template tags to control timezone conversion in templates.
The `timezone` tag allows you to render a datetime in a specific timezone.

<div align="right" style="margin-bottom: -10px;"><a href="https://github.com/epicserve/django-datetime-cheatsheet/tree/wip/tests/test_templates.py#L86-L108" title="View full example in source code" style="font-size: 0.8em; color: #5a5a5a; text-decoration: none;">📝 View full example</a></div>

```python
# Create a fixed datetime in UTC for demonstration purposes
utc_dt = datetime(2024, 1, 2, 0, 0, tzinfo=utc)

# Render a datetime object that has a different timezone than the active timezone
pt_dt = dj_tz.localtime(utc_dt, ZoneInfo("America/Los_Angeles"))
assert pt_dt.strftime("%Y-%m-%d %-I:%M %p") == "2024-01-01 4:00 PM"
assert dj_tz.get_current_timezone_name() == "America/Chicago"
result = render_template("{{ pt_dt }}", {"pt_dt": pt_dt})
assert "Jan. 1, 2024, 6 p.m." in result

# Render a datetime object in a different timezone using the timezone template tag
result = self.render_str_template(
    '{% load tz %}{% timezone "America/Los_Angeles" %}{{ pt_dt }}{% endtimezone %}',
    {"pt_dt": pt_dt},
)
assert "Jan. 1, 2024, 4 p.m." in result
```

### Model Display Methods

Use model methods to display datetimes in the model's timezone.

When working with models that have timezone-specific datetime fields,
it's often useful to create methods that display the datetime in the
model's timezone rather than the current timezone.

<div align="right" style="margin-bottom: -10px;"><a href="https://github.com/epicserve/django-datetime-cheatsheet/tree/wip/tests/test_templates.py#L110-L133" title="View full example in source code" style="font-size: 0.8em; color: #5a5a5a; text-decoration: none;">📝 View full example</a></div>

```python
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

result = self.render_str_template("{{ event.display_start_time }}", {"event": event})
assert "Jan. 1, 2024, 1:30 p.m." in result
```


<!-- section-examples-end -->


## Running the Tests

Everything that was covered in this cheatsheet is based on the tests in the `tests/` directory. To run the 
tests, run the following Just command:

```bash
just test
```

## Updating the README

This README is automatically generated from the test files. If you make changes to the tests,
you can update the README by running:

```bash
just update_readme
```

## See Dynamic Timezone Changes

Run the following Just command to run the Django server:

```bash
just start
```

## Contributing

Contributions are welcome! If you have a datetime-related Django tip or trick that you'd like to add to this cheatsheet,
please open a pull request.

## References

- [Django Documentation on Time Zones](https://docs.djangoproject.com/en/stable/topics/i18n/timezones/)
- [Python datetime module](https://docs.python.org/3/library/datetime.html)
- [Python zoneinfo module](https://docs.python.org/3/library/zoneinfo.html)

[uv]: https://github.com/astral-sh/uv
[just]: https://github.com/casey/just
