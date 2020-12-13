from contextlib import contextmanager
from unittest import mock

import django
from django.db import connection
from django.test import SimpleTestCase, override_settings

from django_version_checks.checks import check_everything


def call_check_everything(databases=None):
    if databases is None:
        databases = ["default"]
    if django.VERSION >= (3, 1):
        return check_everything(app_configs=None, databases=databases)
    else:
        return check_everything(app_configs=None)


class CheckEverythingTests(SimpleTestCase):
    def test_success_no_setting(self):
        errors = call_check_everything()

        assert errors == []

    @override_settings(VERSION_CHECKS=[])
    def test_fail_bad_type(self):
        errors = call_check_everything()

        assert len(errors) == 1
        assert errors[0].id == "dvc.E001"
        assert (
            errors[0].msg
            == "settings.VERSION_CHECKS is misconfigured. Expected a dict but got []."
        )

    @override_settings(VERSION_CHECKS={})
    def test_success_empty_dict(self):
        errors = call_check_everything()

        assert errors == []


class CheckPythonVersionTests(SimpleTestCase):
    @override_settings(VERSION_CHECKS={"python": 3})
    def test_fail_bad_type(self):
        errors = call_check_everything()

        assert len(errors) == 1
        assert errors[0].id == "dvc.E001"
        assert errors[0].msg == (
            "settings.VERSION_CHECKS['python'] is misconfigured. Expected "
            + "a str but got 3."
        )

    @override_settings(VERSION_CHECKS={"python": "3"})
    def test_fail_bad_specifier(self):
        errors = call_check_everything()

        assert len(errors) == 1
        assert errors[0].id == "dvc.E002"
        assert errors[0].msg == (
            "settings.VERSION_CHECKS['python'] is misconfigured. '3' is "
            + "not a valid PEP440 specifier."
        )

    @override_settings(VERSION_CHECKS={"python": "<1.0"})
    def test_fail_out_of_range(self):
        errors = call_check_everything()

        assert len(errors) == 1
        assert errors[0].id == "dvc.E003"
        assert errors[0].msg.startswith("The current version of Python ")
        assert errors[0].msg.endswith("does not match the specified range (<1.0).")

    @override_settings(VERSION_CHECKS={"python": ">=1.0"})
    def test_success_in_range(self):
        errors = call_check_everything()

        assert errors == []


@contextmanager
def fake_postgresql(*, pg_version):
    mock_vendor = mock.patch.object(connection, "vendor", "postgresql")
    mock_pg_version = mock.patch.object(
        connection, "pg_version", pg_version, create=True
    )
    with mock_vendor, mock_pg_version:
        yield


class CheckPostgresqlVersionTests(SimpleTestCase):
    @override_settings(VERSION_CHECKS={"postgresql": 13})
    def test_fail_bad_type(self):
        errors = call_check_everything()

        assert len(errors) == 1
        assert errors[0].id == "dvc.E001"
        assert errors[0].msg == (
            "settings.VERSION_CHECKS['postgresql'] is misconfigured."
            + " Expected a str or dict[str, str] but got 13."
        )

    @override_settings(VERSION_CHECKS={"postgresql": "~=13.1"})
    def test_fail_out_of_range(self):
        with fake_postgresql(pg_version=13_00_00):
            errors = call_check_everything()

        assert len(errors) == 1
        assert errors[0].id == "dvc.E004"
        assert errors[0].msg == (
            "The current version of PostgreSQL (13.0.0) for the default"
            + " database connection does not match the specified range"
            + " (~=13.1)."
        )

    @override_settings(VERSION_CHECKS={"postgresql": "13.1"})
    def test_fail_bad_specifier(self):
        with fake_postgresql(pg_version=13_00_00):
            errors = call_check_everything()

        assert len(errors) == 1
        assert errors[0].id == "dvc.E002"
        assert errors[0].msg == (
            "settings.VERSION_CHECKS['postgresql'] is misconfigured. '13.1' is "
            + "not a valid PEP440 specifier."
        )

    @override_settings(VERSION_CHECKS={"postgresql": {"default": "13.1"}})
    def test_fail_bad_specifier_in_dict(self):
        with fake_postgresql(pg_version=13_00_00):
            errors = call_check_everything()

        assert len(errors) == 1
        assert errors[0].id == "dvc.E002"
        assert errors[0].msg == (
            "settings.VERSION_CHECKS['postgresql'] is misconfigured. '13.1' is "
            + "not a valid PEP440 specifier."
        )

    @override_settings(VERSION_CHECKS={"postgresql": "~=13.1"})
    def test_success_no_postgresql_connections(self):
        errors = call_check_everything()

        assert errors == []

    @override_settings(VERSION_CHECKS={"postgresql": "~=13.1"})
    def test_success_in_range(self):
        with fake_postgresql(pg_version=13_02_00):
            errors = call_check_everything()

        assert errors == []

    @override_settings(VERSION_CHECKS={"postgresql": "~=13.1"})
    def test_success_not_asked_about(self):
        with fake_postgresql(pg_version=13_02_00):
            errors = call_check_everything(databases=["other"])

        assert errors == []

    @override_settings(VERSION_CHECKS={"postgresql": {"default": "~=13.1"}})
    def test_success_in_range_specific_alias(self):
        with fake_postgresql(pg_version=13_02_00):
            errors = call_check_everything()

        assert errors == []

    @override_settings(VERSION_CHECKS={"postgresql": {"other": "~=13.1"}})
    def test_success_specified_other_alias(self):
        with fake_postgresql(pg_version=13_00_00):
            errors = call_check_everything()

        assert errors == []
