from functools import wraps

import django
from django.db import connections

if django.VERSION >= (3, 1):

    def database_check(func):
        return func


else:

    def database_check(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            kwargs.setdefault("databases", list(connections))
            return func(*args, **kwargs)

        return wrapper
