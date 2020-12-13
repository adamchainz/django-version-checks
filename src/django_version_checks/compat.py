from functools import wraps

import django
from django.db import connections

if django.VERSION >= (3, 1):

    def database_check(func):
        return func


else:

    def database_check(func):
        @wraps(func)
        def wrapper(**kwargs):
            return func(databases=list(connections), **kwargs)

        return wrapper
