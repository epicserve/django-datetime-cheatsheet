# Django Datetime Cheat Sheet

This repository was created as a companion to Brent O'Connor's [blog post][blog-post].
Please use this repository as a way to play around with the code examples provided in the blog post. To get started, 
clone this repository and make sure you have [UV][uv] and [Just][just] installed. Then run the following Just command:

```bash
just run_initial_setup
```

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
