from django.apps import AppConfig
from django.core.checks import Tags, register

from django_version_checks import checks


class DjangoVersionChecksAppConfig(AppConfig):
    name = "django_version_checks"
    verbose_name = "django-version-checks"

    def ready(self):
        register(Tags.compatibility)(checks.check_config)
        register(Tags.compatibility)(checks.check_python_version)
        register(Tags.database)(checks.check_postgresql_version)
        register(Tags.database)(checks.check_mysql_version)
        register(Tags.database)(checks.check_sqlite_version)
