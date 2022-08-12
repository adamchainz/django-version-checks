from __future__ import annotations

from typing import Callable, List

from django.core.checks import CheckMessage

CheckFunc = Callable[..., List[CheckMessage]]
