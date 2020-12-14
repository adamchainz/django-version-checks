import django
import wrapt
from django.db import connections

if django.VERSION >= (3, 1):

    def database_check(func):
        return func


else:

    @wrapt.decorator
    def database_check(wrapped, instance, args, kwargs):
        kwargs.setdefault("databases", list(connections))
        return wrapped(*args, **kwargs)
