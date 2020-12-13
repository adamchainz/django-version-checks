from django.test import SimpleTestCase, override_settings

from django_version_checks.checks import check_everything


class CheckEverythingTests(SimpleTestCase):
    def test_success_no_setting(self):
        errors = check_everything()

        assert errors == []

    @override_settings(VERSION_CHECKS=[])
    def test_fail_bad_type(self):
        errors = check_everything()

        assert len(errors) == 1
        assert errors[0].id == "dvc.E001"
        assert (
            errors[0].msg
            == "settings.VERSION_CHECKS is misconfigured. Expected a dict but got []."
        )

    @override_settings(VERSION_CHECKS={})
    def test_success_empty_dict(self):
        errors = check_everything()

        assert errors == []


class CheckPythonVersionTests(SimpleTestCase):
    @override_settings(VERSION_CHECKS={"python": 3})
    def test_fail_bad_type(self):
        errors = check_everything()

        assert len(errors) == 1
        assert errors[0].id == "dvc.E001"
        assert (
            errors[0].msg
            == "settings.VERSION_CHECKS['python'] is misconfigured. Expected a str but got 3."
        )

    @override_settings(VERSION_CHECKS={"python": "3"})
    def test_fail_bad_specifier(self):
        errors = check_everything()

        assert len(errors) == 1
        assert errors[0].id == "dvc.E002"
        assert (
            errors[0].msg
            == "settings.VERSION_CHECKS['python'] is misconfigured. '3' is not a valid PEP440 specifier."
        )

    @override_settings(VERSION_CHECKS={"python": "<1.0"})
    def test_fail_out_of_range(self):
        errors = check_everything()

        assert len(errors) == 1
        assert errors[0].id == "dvc.E003"
        assert errors[0].msg.startswith("The current version of Python ")
        assert errors[0].msg.endswith("does not match the specified range (<1.0).")

    @override_settings(VERSION_CHECKS={"python": ">=1.0"})
    def test_passing(self):
        errors = check_everything()

        assert errors == []
