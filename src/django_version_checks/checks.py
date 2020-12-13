import sys
from functools import wraps

import django
from django.conf import settings
from django.core.checks import Error
from django.db import connections
from packaging.specifiers import InvalidSpecifier, SpecifierSet
from packaging.version import Version


def check_everything(*, app_configs, **kwargs):
    if django.VERSION >= (3, 1):
        databases = set(kwargs["databases"])
    else:
        databases = set(connections)

    if not settings.is_overridden("VERSION_CHECKS"):
        return []

    settings_dict = settings.VERSION_CHECKS
    if not isinstance(settings_dict, dict):
        return [
            bad_type_error(
                name="",
                expected="dict",
                value=settings_dict,
            )
        ]

    errors = []
    if "python" in settings_dict:
        errors.extend(
            check_python_version(
                specifier=settings_dict["python"],
            )
        )
    if "postgresql" in settings_dict:
        errors.extend(
            check_postgresql_version(
                specifiers=settings_dict["postgresql"],
                databases=databases,
            )
        )

    return errors


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


def check_python_version(specifier):
    if not isinstance(specifier, str):
        return [bad_type_error(name="python", expected="str", value=specifier)]

    try:
        specifier_set = SpecifierSet(specifier)
    except InvalidSpecifier:
        return [bad_specifier_error(name="python", value=specifier)]

    version_string = (
        f"{sys.version_info[0]}.{sys.version_info[1]}.{sys.version_info[2]}"
    )
    current_version = Version(version_string)

    errors = []

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


class AnyDict:
    def __init__(self, value):
        self.value = value

    def __contains__(self, key):
        return True

    def __getitem__(self, key):
        return self.value


def parse_specifier_dict(*, name):
    def decorator(func):
        @wraps(func)
        def wrapper(specifiers, *args, **kwargs):
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


@parse_specifier_dict(name="postgresql")
def check_postgresql_version(specifier_dict, databases):
    errors = []
    for alias in connections:
        if alias not in databases:
            continue
        if alias not in specifier_dict:
            continue
        connection = connections[alias]
        if connection.vendor != "postgresql":
            continue
        specifier_set = specifier_dict[alias]

        major = (connection.pg_version // 10_000) % 100
        minor = (connection.pg_version // 100) % 100
        patch = connection.pg_version % 100
        version_string = f"{major}.{minor}.{patch}"
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
