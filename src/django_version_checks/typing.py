from __future__ import annotations

from typing import Callable

from django.core.checks import CheckMessage

CheckFunc = Callable[..., list[CheckMessage]]
