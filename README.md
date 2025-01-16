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
Python 3.13.0 (main, Oct  7 2024, 23:47:22) [Clang 18.1.8 ] on darwin
Type "help", "copyright", "credits" or "license" for more information.
(InteractiveConsole)
>>> 
```

Let's get started, first, let's import the necessary modules:

```python
>>> from datetime import date, datetime, time, timedelta, timezone
>>> from zoneinfo import ZoneInfo
# Import Django's timezone utilities as dj_tz for illustrative purposes and to
# avoid confusion with the built-in timezone module
>>> from django.utils import timezone as dj_tz
>>> # Define UTC for convenience
>>> utc = timezone.utc
```

### Getting the Current Timezone

The current timezone in Django timezone is based on the `TIME_ZONE` setting in your Django settings.

```python
>>> dj_tz.get_current_timezone_name()
'America/Chicago'
```

### Get Current Datetime

Getting the current datetime in UTC is straightforward:

```python
>>> dj_tz.now()
datetime.datetime(2024, 12, 6, 22, 51, 15, 145061, tzinfo=datetime.timezone.utc)
```

> **Notice:** `now()` returns the a datetime object with the UTC timezone.

Get the current datetime in the local timezone:

```python
>>> dj_tz.localtime(dj_tz.now())
datetime.datetime(2024, 12, 6, 16, 51, 15, 145061, tzinfo=zoneinfo.ZoneInfo(key='America/Chicago'))
```

### Naive vs Aware Datetimes

Django distinguishes between "naive" and "aware" datetime objects. Naive datetimes don't have timezone information,
while aware datetimes do.

```python
>>> naive_datetime = datetime(2024, 4, 7, 14, 30)
>>> dj_tz.is_naive(naive_datetime)
True
>>> dj_tz.is_aware(naive_datetime)
False

>>> # Converting naive to aware
>>> aware_datetime = dj_tz.make_aware(naive_datetime)
>>> aware_datetime
datetime.datetime(2024, 4, 7, 14, 30, tzinfo=zoneinfo.ZoneInfo(key='America/Chicago'))
>>> dj_tz.is_aware(aware_datetime)
True
>>> dj_tz.is_naive(aware_datetime)
False
```

### Timezone Conversions

You can create and convert datetimes between different timezones:

```python
>>> # Create a UTC datetime
>>> utc_dt = datetime(2024, 10, 1, 13, 30, tzinfo=utc)
>>> # Convert to local time
>>> local_dt = dj_tz.localtime(utc_dt)
>>> local_dt
datetime.datetime(2024, 10, 1, 8, 30, tzinfo=zoneinfo.ZoneInfo(key='America/Chicago'))

>>> # Convert to Mountain time
>>> mountain_datetime = dj_tz.localtime(local_dt, timezone=ZoneInfo("US/Mountain"))
>>> mountain_datetime
datetime.datetime(2024, 10, 1, 7, 30, tzinfo=zoneinfo.ZoneInfo(key='US/Mountain'))
```

### Handling Date Boundaries

Be careful when working with dates across timezones. For example, 6 PM on January 1st in Central time is actually
January 2nd in UTC:

```python
>>> local_dt = datetime(2024, 1, 1, 18, 0, tzinfo=ZoneInfo("US/Central"))
>>> utc_dt_next_day = dj_tz.localtime(local_dt, timezone=utc)
>>> utc_dt_next_day.date()
datetime.date(2024, 1, 2)
>>> # Use localdate to get the date in local time
>>> dj_tz.localdate(utc_dt_next_day)
datetime.date(2024, 1, 1)
```

### Changing Active Timezone

You can temporarily change the active timezone for the current thread. This is useful when you need to perform
operations in a different timezone.

```python
>>> dj_tz.get_current_timezone_name()
'America/Chicago'
>>> dj_tz.activate(ZoneInfo("US/Eastern"))
>>> dj_tz.get_current_timezone_name()
'US/Eastern'
>>> dj_tz.deactivate()  # Reset to default
>>> dj_tz.get_current_timezone_name()
'America/Chicago'
```

Use the `override` context manager to temporarily change the timezone:

```python
with dj_tz.override(ZoneInfo("America/Los_Angeles")):
    event_start_time = dj_tz.make_aware(datetime(2024, 1, 1, 22, 30))
    event_end_time = event_start_time + timedelta(hours=1)
    event = baker.make("events.Event")
    event.start_time = event_start_time
    event.end_time = event_end_time
    event.save()
```

## Formatting Datetime Objects

Django provides several ways to format datetime objects into strings.

### Using Django's dateformat Module

```python
>>> from django.utils import dateformat
>>> utc_dt = datetime(2024, 10, 1, 13, 30, tzinfo=utc)
>>> dateformat.format(utc_dt, settings.DATETIME_FORMAT)
'Oct. 1, 2024, 1:30 p.m.'
```

<div class="notice notice-warning">
  <strong>Warning:</strong> The `dateformat` module doesn't handle timezone conversion.
</div>

If you need to convert to local time, you can use Django's `localtime` you can make a wrapper function for convenience:

```python
>>> def local_format(value, format_string):
...     return dateformat.format(dj_tz.localtime(value), format_string)
...
>>> local_format(utc_dt, settings.DATETIME_FORMAT)
'Oct. 1, 2024, 8:30 a.m.'
```

## Template Formatting

When working with datetimes in Django templates, the date filter automatically handles timezone conversion:

```python
{% raw %}
>>> from django.template import Template, Context
>>> utc_dt = datetime(2024, 1, 2, 0, 0, tzinfo=utc)

>>> # Default format
>>> Template("{{ utc_dt }}").render(Context({"utc_dt": utc_dt}))
'Jan. 1, 2024, 6 p.m.'

>>> # Custom format
>>> Template("{{ utc_dt|date:'DATE_FORMAT' }}").render(Context({"utc_dt": utc_dt}))
'Jan. 1, 2024'

>>> # Format for JavaScript
>>> Template("{{ utc_dt|date:'c' }}").render(Context({"utc_dt": utc_dt}))
'2024-01-01T18:00:00-06:00'
{% endraw %}
```

## Testing with Mocked Dates

When testing datetime-dependent code, you can mock the current time to ensure consistent results and avoid issues with
tests randomly failing due to time differences. It's recommended that when mocking datetime objects in tests, that you
use datetime objects enough mocked datetime objects to cover all of your logic cases.

```python
>>> from unittest.mock import patch
>>> with patch('django.utils.timezone.now') as mock_now:
...     mock_now.return_value = datetime(2019, 1, 2, 0, 0, tzinfo=utc)
...     assert dj_tz.now() == datetime(2019, 1, 2, 0, 0, tzinfo=utc)
```

This guide covers the basics of working with dates and times in Django. Remember to always be mindful of timezones when
handling datetime objects, and use Django's built-in utilities to ensure consistent behavior across your application.










## Tests

Everything that was covered in the [blog post][blog-post] was done based on the tests
(`apps/base/tests/test_datetime.py`) in this repository. To run the 
tests, run the following Just command:

```bash
just test
```


## See Dynamic Timezone Changes

Run the following Just command to run the Django server:

```bash
just start
```

Once the server is running, you can navigate to http://localhost:8000 to login in. Then in the 
[Django admin](http://localhost:8000/admin/accounts/user/), change your user's timezone to one your not in and then go 
back to the home page. You should see modal appear that asks if you want to change your timezone to reflect your 
current timezone.


[blog-post]: https://epicserve.com/django/2025/01/14/django-datetime-cheatsheet.html
[uv]: https://docs.astral.sh/uv/getting-started/installation/
[just]: https://github.com/casey/just?tab=readme-ov-file#installation
