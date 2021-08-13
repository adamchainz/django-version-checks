import sys
from functools import wraps
from typing import Any, Callable, Dict, Generator, List, Optional, Tuple, Union, cast

from django.conf import settings
from django.core.checks import Error
from django.db import connections
from django.db.backends.base.base import BaseDatabaseWrapper
from packaging.specifiers import InvalidSpecifier, SpecifierSet
from packaging.version import Version

from django_version_checks.compat import database_check
from django_version_checks.typing import CheckFunc


def check_config(**kwargs: Any) -> List[Error]:
    errors = []

    if settings.is_overridden("VERSION_CHECKS"):
        settings_dict = settings.VERSION_CHECKS
        if not isinstance(settings_dict, dict):
            errors.append(
                bad_type_error(
                    name="",
                    expected="dict",
                    value=settings_dict,
                )
            )

    return errors


def get_config() -> Dict[str, Union[str, Dict[str, str]]]:
    if not settings.is_overridden("VERSION_CHECKS"):
        return {}
    if isinstance(settings.VERSION_CHECKS, dict):
        return settings.VERSION_CHECKS
    return {}


def bad_type_error(*, name: str, expected: str, value: object) -> Error:
    label = "settings.VERSION_CHECKS"
    if name:
        label += f"[{name!r}]"
    return Error(
        id="dvc.E001",
        msg=f"{label} is misconfigured. Expected a {expected} but got {value!r}.",
    )


def bad_specifier_error(*, name: str, value: object) -> Error:
    return Error(
        id="dvc.E002",
        msg=(
            f"settings.VERSION_CHECKS[{name!r}] is misconfigured. {value!r}"
            + " is not a valid PEP440 specifier."
        ),
    )


def parse_specifier_str(*, name: str) -> Callable[[CheckFunc], CheckFunc]:
    def decorator(func: CheckFunc) -> CheckFunc:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> List[Error]:
            config = get_config()
            if name not in config:
                return []
            specifier = config[name]
            if not isinstance(specifier, str):
                return [bad_type_error(name=name, expected="str", value=specifier)]

            try:
                specifier_set = SpecifierSet(specifier)
            except InvalidSpecifier:
                return [bad_specifier_error(name=name, value=specifier)]

            return func(specifier_set, *args, **kwargs)

        return cast(CheckFunc, wrapper)

    return decorator


class AnyDict(Dict[str, str]):
    def __init__(self, value: str) -> None:
        self.value = value

    def __getitem__(self, key: str) -> str:
        return self.value


def parse_specifier_str_or_dict(*, name: str) -> Callable[[CheckFunc], CheckFunc]:
    def decorator(func: CheckFunc) -> CheckFunc:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> List[Error]:
            config = get_config()
            if name not in config:
                return []
            specifiers = config[name]

            specifier_dict: Dict[str, str]
            if isinstance(specifiers, str):
                try:
                    specifier_set = SpecifierSet(specifiers)
                except InvalidSpecifier:
                    return [bad_specifier_error(name=name, value=specifiers)]
                specifier_dict = AnyDict(specifier_set)
            elif (
                isinstance(specifiers, dict)
                and all(isinstance(a, str) for a in specifiers.keys())
                and all(isinstance(s, str) for s in specifiers.values())
            ):
                specifier_dict = {}
                for alias, specifier in specifiers.items():
                    try:
                        specifier_set = SpecifierSet(specifier)
                    except InvalidSpecifier:
                        return [bad_specifier_error(name=name, value=specifier)]
                    specifier_dict[alias] = specifier_set
            else:
                return [
                    bad_type_error(
                        name=name,
                        expected="str or dict[str, str]",
                        value=specifiers,
                    )
                ]

            return func(specifier_dict, *args, **kwargs)

        return cast(CheckFunc, wrapper)

    return decorator


def db_connections_matching(
    databases: Optional[List[str]],
    vendor: str,
) -> Generator[Tuple[str, BaseDatabaseWrapper], None, None]:
    if databases is None:
        databases_set = set()
    else:
        databases_set = set(databases)

    for alias in connections:
        if alias not in databases_set:
            continue
        connection = connections[alias]
        if connection.vendor != vendor:
            continue
        yield alias, connection


@parse_specifier_str(name="python")
def check_python_version(specifier_set: SpecifierSet, **kwargs: Any) -> List[Error]:
    errors = []

    version_string = (
        f"{sys.version_info[0]}.{sys.version_info[1]}.{sys.version_info[2]}"
    )
    current_version = Version(version_string)

    if current_version not in specifier_set:
        errors.append(
            Error(
                id="dvc.E003",
                msg=(
                    f"The current version of Python ({version_string}) does"
                    + f" not match the specified range ({specifier_set})."
                ),
            )
        )

    return errors


@database_check
@parse_specifier_str_or_dict(name="postgresql")
def check_postgresql_version(
    specifier_dict: Dict[str, str],
    databases: Optional[List[str]],
    **kwargs: Any,
) -> List[Error]:
    errors = []
    for alias, connection in db_connections_matching(databases, "postgresql"):
        try:
            specifier_set = specifier_dict[alias]
        except KeyError:
            continue

        # See: https://www.postgresql.org/docs/current/libpq-status.html#LIBPQ-PQSERVERVERSION  # noqa: B950
        pg_version = connection.pg_version
        major = (pg_version // 10_000) % 100
        if major < 10:
            minor = (pg_version // 100) % 100
            patch = pg_version % 100
            version_string = f"{major}.{minor}.{patch}"
        else:
            minor = pg_version % 10_000
            version_string = f"{major}.{minor}"
        postgresql_version = Version(version_string)

        if postgresql_version not in specifier_set:
            errors.append(
                Error(
                    id="dvc.E004",
                    msg=(
                        f"The current version of PostgreSQL ({version_string})"
                        + f" for the {alias} database connection does not match"
                        + f" the specified range ({specifier_set})."
                    ),
                )
            )

    return errors


@database_check
@parse_specifier_str_or_dict(name="mysql")
def check_mysql_version(
    specifier_dict: Dict[str, str],
    databases: Optional[List[str]],
    **kwargs: Any,
) -> List[Error]:
    errors = []
    for alias, connection in db_connections_matching(databases, "mysql"):
        try:
            specifier_set = specifier_dict[alias]
        except KeyError:
            continue

        version_string = ".".join(str(i) for i in connection.mysql_version)
        mysql_version = Version(version_string)

        if mysql_version not in specifier_set:
            errors.append(
                Error(
                    id="dvc.E005",
                    msg=(
                        "The current version of MariaDB/MySQL"
                        + f" ({version_string}) for the {alias} database"
                        + " connection does not match the specified range"
                        + f" ({specifier_set})."
                    ),
                )
            )

    return errors


@parse_specifier_str(name="sqlite")
def check_sqlite_version(specifier_set: SpecifierSet, **kwargs: Any) -> List[Error]:
    from sqlite3.dbapi2 import sqlite_version_info

    errors = []

    version_string = ".".join(str(i) for i in sqlite_version_info)
    sqlite_version = Version(version_string)

    if sqlite_version not in specifier_set:
        errors.append(
            Error(
                id="dvc.E006",
                msg=(
                    f"The current version of SQLite ({version_string}) does"
                    + f" not match the specified range ({specifier_set})."
                ),
            )
        )

    return errors
