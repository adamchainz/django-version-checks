from contextlib import contextmanager
from unittest import mock

from django.db import connection
from django.test import SimpleTestCase, override_settings

from django_version_checks import checks


class CheckConfigTests(SimpleTestCase):
    def test_success_no_setting(self):
        errors = checks.check_config()

        assert errors == []

    @override_settings(VERSION_CHECKS=[])
    def test_fail_bad_type(self):
        errors = checks.check_config()

        assert len(errors) == 1
        assert errors[0].id == "dvc.E001"
        assert (
            errors[0].msg
            == "settings.VERSION_CHECKS is misconfigured. Expected a dict but got []."
        )

    @override_settings(VERSION_CHECKS={})
    def test_success_empty_dict(self):
        errors = checks.check_config()

        assert errors == []


class GetConfigTests(SimpleTestCase):
    def test_no_setting(self):
        config = checks.get_config()

        assert config == {}

    @override_settings(VERSION_CHECKS={"something": "here"})
    def test_setting(self):
        config = checks.get_config()

        assert config == {"something": "here"}

    @override_settings(VERSION_CHECKS=["woops"])
    def test_bad_setting(self):
        config = checks.get_config()

        assert config == {}


class CheckPythonVersionTests(SimpleTestCase):
    @override_settings(VERSION_CHECKS={"python": 3})
    def test_fail_bad_type(self):
        errors = checks.check_python_version()

        assert len(errors) == 1
        assert errors[0].id == "dvc.E001"
        assert errors[0].msg == (
            "settings.VERSION_CHECKS['python'] is misconfigured. Expected "
            + "a str but got 3."
        )

    @override_settings(VERSION_CHECKS={"python": "3"})
    def test_fail_bad_specifier(self):
        errors = checks.check_python_version()

        assert len(errors) == 1
        assert errors[0].id == "dvc.E002"
        assert errors[0].msg == (
            "settings.VERSION_CHECKS['python'] is misconfigured. '3' is "
            + "not a valid PEP440 specifier."
        )

    @override_settings(VERSION_CHECKS={"python": "<1.0"})
    def test_fail_out_of_range(self):
        errors = checks.check_python_version()

        assert len(errors) == 1
        assert errors[0].id == "dvc.E003"
        assert errors[0].msg.startswith("The current version of Python ")
        assert errors[0].msg.endswith("does not match the specified range (<1.0).")

    @override_settings(VERSION_CHECKS={"python": ">=1.0"})
    def test_success_in_range(self):
        errors = checks.check_python_version()

        assert errors == []

    @override_settings(VERSION_CHECKS={})
    def test_success_unspecified(self):
        errors = checks.check_python_version()

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
        errors = checks.check_postgresql_version(databases=["default"])

        assert len(errors) == 1
        assert errors[0].id == "dvc.E001"
        assert errors[0].msg == (
            "settings.VERSION_CHECKS['postgresql'] is misconfigured."
            + " Expected a str or dict[str, str] but got 13."
        )

    @override_settings(VERSION_CHECKS={"postgresql": "13.1"})
    def test_fail_bad_specifier(self):
        errors = checks.check_postgresql_version(databases=["default"])

        assert len(errors) == 1
        assert errors[0].id == "dvc.E002"
        assert errors[0].msg == (
            "settings.VERSION_CHECKS['postgresql'] is misconfigured. '13.1' is "
            + "not a valid PEP440 specifier."
        )

    @override_settings(VERSION_CHECKS={"postgresql": {"default": "13.1"}})
    def test_fail_bad_specifier_in_dict(self):
        errors = checks.check_postgresql_version(databases=["default"])

        assert len(errors) == 1
        assert errors[0].id == "dvc.E002"
        assert errors[0].msg == (
            "settings.VERSION_CHECKS['postgresql'] is misconfigured. '13.1' is "
            + "not a valid PEP440 specifier."
        )

    @override_settings(VERSION_CHECKS={"postgresql": "~=13.1"})
    def test_old_version_out_of_range(self):
        with fake_postgresql(pg_version=9_01_05):
            errors = checks.check_postgresql_version(databases=["default"])

        assert len(errors) == 1
        assert errors[0].id == "dvc.E004"
        assert errors[0].msg == (
            "The current version of PostgreSQL (9.1.5) for the default"
            + " database connection does not match the specified range"
            + " (~=13.1)."
        )

    @override_settings(VERSION_CHECKS={"postgresql": "~=13.1"})
    def test_fail_out_of_range(self):
        with fake_postgresql(pg_version=13_00_00):
            errors = checks.check_postgresql_version(databases=["default"])

        assert len(errors) == 1
        assert errors[0].id == "dvc.E004"
        assert errors[0].msg == (
            "The current version of PostgreSQL (13.0) for the default"
            + " database connection does not match the specified range"
            + " (~=13.1)."
        )

    @override_settings(VERSION_CHECKS={"postgresql": "~=13.1"})
    def test_success_no_postgresql_connections(self):
        errors = checks.check_postgresql_version(databases=["default"])

        assert errors == []

    @override_settings(VERSION_CHECKS={"postgresql": "~=13.1"})
    def test_success_in_range(self):
        with fake_postgresql(pg_version=13_02_00):
            errors = checks.check_postgresql_version(databases=["default"])

        assert errors == []

    @override_settings(VERSION_CHECKS={"postgresql": "~=13.1"})
    def test_success_not_asked_about(self):
        with fake_postgresql(pg_version=13_02_00):
            errors = checks.check_postgresql_version(databases=["other"])

        assert errors == []

    @override_settings(VERSION_CHECKS={"postgresql": "~=13.1"})
    def test_success_databases_none(self):
        with fake_postgresql(pg_version=13_02_00):
            errors = checks.check_postgresql_version(databases=None)

        assert errors == []

    @override_settings(VERSION_CHECKS={"postgresql": {"default": "~=13.1"}})
    def test_success_in_range_specific_alias(self):
        with fake_postgresql(pg_version=13_02_00):
            errors = checks.check_postgresql_version(databases=["default"])

        assert errors == []

    @override_settings(VERSION_CHECKS={"postgresql": {"other": "~=13.1"}})
    def test_success_specified_other_alias(self):
        with fake_postgresql(pg_version=13_00_00):
            errors = checks.check_postgresql_version(databases=["default"])

        assert errors == []

    @override_settings(VERSION_CHECKS={})
    def test_success_unspecified(self):
        errors = checks.check_postgresql_version(databases=["default"])

        assert errors == []


@contextmanager
def fake_mysql(*, mysql_version):
    mock_vendor = mock.patch.object(connection, "vendor", "mysql")
    mock_mysql_version = mock.patch.object(
        connection, "mysql_version", mysql_version, create=True
    )
    with mock_vendor, mock_mysql_version:
        yield


class CheckMysqlVersionTests(SimpleTestCase):
    @override_settings(VERSION_CHECKS={"mysql": 10})
    def test_fail_bad_type(self):
        errors = checks.check_mysql_version(databases=["default"])

        assert len(errors) == 1
        assert errors[0].id == "dvc.E001"
        assert errors[0].msg == (
            "settings.VERSION_CHECKS['mysql'] is misconfigured."
            + " Expected a str or dict[str, str] but got 10."
        )

    @override_settings(VERSION_CHECKS={"mysql": "10.5.8"})
    def test_fail_bad_specifier(self):
        errors = checks.check_mysql_version(databases=["default"])

        assert len(errors) == 1
        assert errors[0].id == "dvc.E002"
        assert errors[0].msg == (
            "settings.VERSION_CHECKS['mysql'] is misconfigured. '10.5.8' is "
            + "not a valid PEP440 specifier."
        )

    @override_settings(VERSION_CHECKS={"mysql": {"default": "10.5.8"}})
    def test_fail_bad_specifier_in_dict(self):
        errors = checks.check_mysql_version(databases=["default"])

        assert len(errors) == 1
        assert errors[0].id == "dvc.E002"
        assert errors[0].msg == (
            "settings.VERSION_CHECKS['mysql'] is misconfigured. '10.5.8' is "
            + "not a valid PEP440 specifier."
        )

    @override_settings(VERSION_CHECKS={"mysql": "~=10.5.8"})
    def test_fail_out_of_range(self):
        with fake_mysql(mysql_version=(10, 5, 7)):
            errors = checks.check_mysql_version(databases=["default"])

        assert len(errors) == 1
        assert errors[0].id == "dvc.E005"
        assert errors[0].msg == (
            "The current version of MariaDB/MySQL (10.5.7) for the default"
            + " database connection does not match the specified range"
            + " (~=10.5.8)."
        )

    @override_settings(VERSION_CHECKS={"mysql": "~=10.5.8"})
    def test_success_no_mysql_connections(self):
        errors = checks.check_mysql_version(databases=["default"])

        assert errors == []

    @override_settings(VERSION_CHECKS={"mysql": "~=10.5.8"})
    def test_success_in_range(self):
        with fake_mysql(mysql_version=(10, 5, 9)):
            errors = checks.check_mysql_version(databases=["default"])

        assert errors == []

    @override_settings(VERSION_CHECKS={"mysql": "~=10.5.8"})
    def test_success_not_asked_about(self):
        with fake_mysql(mysql_version=(10, 5, 7)):
            errors = checks.check_mysql_version(databases=["other"])

        assert errors == []

    @override_settings(VERSION_CHECKS={"mysql": {"default": "~=10.5.8"}})
    def test_success_in_range_specific_alias(self):
        with fake_mysql(mysql_version=(10, 5, 8)):
            errors = checks.check_mysql_version(databases=["default"])

        assert errors == []

    @override_settings(VERSION_CHECKS={"mysql": {"other": "~=10.5.8"}})
    def test_success_specified_other_alias(self):
        with fake_mysql(mysql_version=(10, 5, 7)):
            errors = checks.check_mysql_version(databases=["default"])

        assert errors == []

    @override_settings(VERSION_CHECKS={})
    def test_success_unspecified(self):
        errors = checks.check_mysql_version(databases=["default"])

        assert errors == []


class CheckSqliteVersionTests(SimpleTestCase):
    @override_settings(VERSION_CHECKS={"sqlite": 3})
    def test_fail_bad_type(self):
        errors = checks.check_sqlite_version()

        assert len(errors) == 1
        assert errors[0].id == "dvc.E001"
        assert errors[0].msg == (
            "settings.VERSION_CHECKS['sqlite'] is misconfigured. Expected "
            + "a str but got 3."
        )

    @override_settings(VERSION_CHECKS={"sqlite": "3"})
    def test_fail_bad_specifier(self):
        errors = checks.check_sqlite_version()

        assert len(errors) == 1
        assert errors[0].id == "dvc.E002"
        assert errors[0].msg == (
            "settings.VERSION_CHECKS['sqlite'] is misconfigured. '3' is "
            + "not a valid PEP440 specifier."
        )

    @override_settings(VERSION_CHECKS={"sqlite": "<1.0"})
    def test_fail_out_of_range(self):
        errors = checks.check_sqlite_version()

        assert len(errors) == 1
        assert errors[0].id == "dvc.E006"
        assert errors[0].msg.startswith("The current version of SQLite ")
        assert errors[0].msg.endswith("does not match the specified range (<1.0).")

    @override_settings(VERSION_CHECKS={"sqlite": ">=3.0"})
    def test_success_in_range(self):
        errors = checks.check_sqlite_version()

        assert errors == []

    @override_settings(VERSION_CHECKS={})
    def test_success_unspecified(self):
        errors = checks.check_sqlite_version()

        assert errors == []
