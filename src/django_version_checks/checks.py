import sys
from functools import wraps

from django.conf import settings
from django.core.checks import Error
from django.db import connections
from packaging.specifiers import InvalidSpecifier, SpecifierSet
from packaging.version import Version

from django_version_checks.compat import database_check


def check_config(**kwargs):
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


def get_config():
    if not settings.is_overridden("VERSION_CHECKS"):
        return {}
    if isinstance(settings.VERSION_CHECKS, dict):
        return settings.VERSION_CHECKS
    return {}


def bad_type_error(*, name, expected, value):
    label = "settings.VERSION_CHECKS"
    if name:
        label += f"[{name!r}]"
    return Error(
        id="dvc.E001",
        msg=(
            f"{label} is misconfigured. Expected a {expected} but got" + f" {value!r}."
        ),
    )


def bad_specifier_error(*, name, value):
    return Error(
        id="dvc.E002",
        msg=(
            f"settings.VERSION_CHECKS[{name!r}] is misconfigured. {value!r}"
            + " is not a valid PEP440 specifier."
        ),
    )


def parse_specifier_str(*, name):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
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

        return wrapper

    return decorator


class AnyDict:
    def __init__(self, value):
        self.value = value

    def __getitem__(self, key):
        return self.value


def parse_specifier_str_or_dict(*, name):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):

            config = get_config()
            if name not in config:
                return []
            specifiers = config[name]

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

        return wrapper

    return decorator


def db_connections_matching(databases, vendor):
    if databases is None:
        databases = set()
    else:
        databases = set(databases)

    for alias in connections:
        if alias not in databases:
            continue
        connection = connections[alias]
        if connection.vendor != vendor:
            continue
        yield alias, connection


@parse_specifier_str(name="python")
def check_python_version(specifier_set, **kwargs):
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
def check_postgresql_version(specifier_dict, databases, **kwargs):
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
def check_mysql_version(specifier_dict, databases, **kwargs):
    errors = []
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
def check_sqlite_version(specifier_set, **kwargs):
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
