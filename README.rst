=====================
django-version-checks
=====================

.. image:: https://img.shields.io/github/workflow/status/adamchainz/django-version-checks/CI/master?style=for-the-badge
   :target: https://github.com/adamchainz/django-version-checks/actions?workflow=CI

.. image:: https://img.shields.io/coveralls/github/adamchainz/django-version-checks/master?style=for-the-badge
   :target: https://app.codecov.io/gh/adamchainz/django-version-checks

.. image:: https://img.shields.io/pypi/v/django-version-checks.svg?style=for-the-badge
   :target: https://pypi.org/project/django-version-checks/

.. image:: https://img.shields.io/badge/code%20style-black-000000.svg?style=for-the-badge
   :target: https://github.com/psf/black

.. image:: https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit&logoColor=white&style=for-the-badge
   :target: https://github.com/pre-commit/pre-commit
   :alt: pre-commit

System checks for your project's environment.

Requirements
============

Python 3.6 to 3.9 supported.

Django 2.2 to 3.2 supported.

----

**Are your tests slow?**
Check out my book `Speed Up Your Django Tests <https://gumroad.com/l/suydt>`__ which covers loads of best practices so you can write faster, more accurate tests.

----

Installation
============

First, install with **pip**:

.. code-block:: bash

    python -m pip install django-version-checks

Second, add the app to your ``INSTALLED_APPS`` setting:

.. code-block:: python

    INSTALLED_APPS = [
        ...
        "django_version_checks",
        ...
    ]

Third, add a ``VERSION_CHECKS`` setting with the version checks you want to enforce (as documented below).
For example:

.. code-block:: python

    VERSION_CHECKS = {
        "python": "==3.9.*",
    }

Usage
=====

See also the `introductory blog post <https://adamj.eu/tech/2020/12/14/introducing-django-version-checks/>`__.

django-version-checks adds several `system checks <https://docs.djangoproject.com/en/stable/topics/checks/>`__ that can help ensure that the current environment has the right versions of Python, databases, etc.
This is useful when coordinating upgrades across all your infrastructure.

Note that django-version-checks does not check the versions of your Python dependencies.
This is because such checks need doing at the start of the Python process, in your `manage.py` file, before Django imports your apps.
Any mismatched versions are likely to cause import time problems, before django-version-checks’ system checks can execute.
To add checks on your Python dependencies, check out `pip-lock <https://github.com/adamchainz/pip-lock/>`__.

Checks use the `PEP 440 specifier format <https://www.python.org/dev/peps/pep-0440/#id53>`__ via the ``packaging`` module.
This is the same format used by pip, and allows some flexibility in specifying valid version ranges.
The ``~=`` operator is particularly useful.
For example, you can use ``~=3.9.1`` to mean “3.9.1+, but less than 3.10.0”, allowing environments to take on patch releases without changes, but nothing more.

The individual checks are documented below.
Each occupies a key in the ``VERSION_CHECKS`` dictionary, and documents its supported types for specifiers.
If a check is misconfigured with a bad type or specifier you will see one of these system check errors:

* ``dvc.E001``: ``<check>`` is misconfigured. Expected a ``<type>`` but got ``<value>``.
* ``dvc.E002``: ``<check>`` is misconfigured. ``<value>`` is not a valid PEP440 specifier.

``mysql`` check
----------------

This check compares the current version of MariaDB/MySQL to the given specifier.
The range can specified either as a single string:

.. code-block:: python

    VERSION_CHECKS = {
        "mysql": "~=10.5.8",
    }

...or as a dictionary mapping database aliases to their specifiers:

.. code-block:: python

    VERSION_CHECKS = {
        "postgresql": {
            "default": "~=10.5.8",
            "analytics": "~=10.4.17",
        },
    }

Note: as a database check, Django will only run this during ``migrate`` or when using ``check --database`` (Django 3.1+) / ``check --tags database`` (Django <3.1).
See (`docs <https://docs.djangoproject.com/en/3.1/ref/checks/#builtin-tags>`__).

If this check fails, the system check will report:

* ``dvc.E005``: The current version of MariaDB/MySQL (``<version>``) for the ``<alias>`` database connection does not match the specified range (``<range>``).

``python`` check
----------------

This check compares the current version of Python to the given single specifier:

.. code-block:: python

    VERSION_CHECKS = {
        "python": "~=3.9.1",
    }

If this check fails, the system check will report:

* ``dvc.E003``: The current version of Python (``<version>``) does not match the specified range (``<range>``).

``postgresql`` check
--------------------

This check compares the current version of PostgreSQL to the given specifier.
The range can specified either as a single string:

.. code-block:: python

    VERSION_CHECKS = {
        "postgresql": "~=12.2",
    }

...or as a dictionary mapping database aliases to their specifiers:

.. code-block:: python

    VERSION_CHECKS = {
        "postgresql": {
            "default": "~=12.2",
            "analytics": "~=13.1",
        },
    }

Note: as a database check, Django will only run this during ``migrate`` or when using ``check --database`` (Django 3.1+) / ``check --tags database`` (Django <3.1).
See (`docs <https://docs.djangoproject.com/en/3.1/ref/checks/#builtin-tags>`__).

If this check fails, the system check will report:

* ``dvc.E004``: The current version of PostgreSQL (``<version>``) for the ``<alias>`` database connection does not match the specified range (``<range>``).

``sqlite`` check
--------------------

This check compares the current version of SQLite to the given single specifier:

.. code-block:: python

    VERSION_CHECKS = {
        "sqlite": "~=12.2",
    }

Note: as a database check, Django will only run this during ``migrate`` or when using ``check --database`` (Django 3.1+) / ``check --tags database`` (Django <3.1).
See (`docs <https://docs.djangoproject.com/en/3.1/ref/checks/#builtin-tags>`__).

If this check fails, the system check will report:

* ``dvc.E006``: The current version of SQLite (``<version>``) does not match the specified range (``<range>``).

Example Upgrade
===============

Let’s walk through using django-version-checks to upgrade Python from version 3.8 to 3.9.
We have an infrastructure consisting of CI, staging, and production environments, and several developers’ development machines.

First, we add a pre-existing check to ensure that all environments are on Python 3.8:

.. code-block:: python

    VERSION_CHECKS = {
        "python": "~=3.8.6",
    }

Second, we rewrite the specifier to allow versions of Python 3.9:

.. code-block:: python

    VERSION_CHECKS = {
        "python": ">=3.8.6,<3.10.0",
    }

Third, we upgrade our infrastructure.
We’d probably upgrade in the order: CI, development environments, staging, production.
Each environment should have an automated run of ``manage.py check``, as per the `Django deployment checklist <https://docs.djangoproject.com/en/3.0/howto/deployment/checklist/>`__.

Fourth, we change the specifier again to allow Python 3.9 only:

.. code-block:: python

    VERSION_CHECKS = {
        "python": "~=3.9.1",
    }

And we’re upgraded! 🎉
