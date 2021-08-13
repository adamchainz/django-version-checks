from functools import wraps
from typing import Any, cast

import django
from django.db import connections

from django_version_checks.typing import CheckFunc

if django.VERSION >= (3, 1):

    def database_check(func: CheckFunc) -> CheckFunc:
        return func


else:

    def database_check(func: CheckFunc) -> CheckFunc:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            kwargs.setdefault("databases", list(connections))
            return func(*args, **kwargs)

        return cast(CheckFunc, wrapper)
