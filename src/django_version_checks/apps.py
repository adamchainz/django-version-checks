from django.apps import AppConfig
from django.core.checks import Tags, register

from django_version_checks.checks import check_everything


class DjangoVersionChecksAppConfig(AppConfig):
    name = "django_version_checks"
    verbose_name = "django-version-checks"

    def ready(self):
        register(Tags.compatibility)(check_everything)
