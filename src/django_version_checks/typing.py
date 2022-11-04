from __future__ import annotations

from typing import Callable
from typing import List

from django.core.checks import CheckMessage

CheckFunc = Callable[..., List[CheckMessage]]
