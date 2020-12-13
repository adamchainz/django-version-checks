import sys

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
        errors.extend(check_python_version(settings_dict["python"]))
    if "postgresql" in settings_dict:
        errors.extend(check_postgresql_version(settings_dict["postgresql"], databases))

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


def check_postgresql_version(specifiers, databases):
    postgresql_connections = {
        alias: connections[alias]
        for alias in connections
        if connections[alias].vendor == "postgresql" and alias in databases
    }

    if isinstance(specifiers, str):
        specifiers = {alias: specifiers for alias in postgresql_connections}
    elif (
        isinstance(specifiers, dict)
        and all(isinstance(a, str) for a in specifiers.keys())
        and all(isinstance(s, str) for s in specifiers.values())
    ):
        pass
    else:
        return [
            bad_type_error(
                name="postgresql",
                expected="str or dict[str, str]",
                value=specifiers,
            )
        ]

    errors = []
    for alias, connection in postgresql_connections.items():
        if alias not in specifiers:
            continue

        specifier = specifiers[alias]
        try:
            specifier_set = SpecifierSet(specifier)
        except InvalidSpecifier:
            return [bad_specifier_error(name="postgresql", value=specifier)]

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
