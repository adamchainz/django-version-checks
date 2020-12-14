import django
import wrapt
from django.db import connections

if django.VERSION >= (3, 1):

    def database_check(func):
        return func


else:

    def database_check(func):
        @wrapt.decorator
        def wrapper(wrapped, instance, args, kwargs):
            kwargs.setdefault("databases", list(connections))
            return wrapped(*args, **kwargs)

        return wrapper
