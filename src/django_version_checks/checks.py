import sys

from django.conf import settings
from django.core.checks import Error
from packaging.specifiers import InvalidSpecifier, SpecifierSet
from packaging.version import Version


def check_everything(*, app_configs=None, **kwargs):
    if not settings.is_overridden("VERSION_CHECKS"):
        return []
    settings_dict = settings.VERSION_CHECKS
    if not isinstance(settings_dict, dict):
        return [
            bad_type_error(
                name="",
                expected=dict,
                value=settings_dict,
            )
        ]

    errors = []
    if "python" in settings_dict:
        errors.extend(check_python_version(settings_dict["python"]))

    return errors


def bad_type_error(*, name, expected, value):
    label = "settings.VERSION_CHECKS"
    if name:
        label += f"[{name!r}]"
    return Error(
        id="dvc.E001",
        msg=f"{label} is misconfigured. Expected a {expected.__name__} but got {value!r}.",
    )


def bad_specifier_error(*, name, value):
    return Error(
        id="dvc.E002",
        msg=(
            f"settings.VERSION_CHECKS[{name!r}] is misconfigured. {value!r}"
            + " is not a valid PEP440 specifier."
        ),
    )


def check_python_version(specifier_string):
    if not isinstance(specifier_string, str):
        return [bad_type_error(name="python", expected=str, value=specifier_string)]

    try:
        specifier_set = SpecifierSet(specifier_string)
    except InvalidSpecifier:
        return [bad_specifier_error(name="python", value=specifier_string)]

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
