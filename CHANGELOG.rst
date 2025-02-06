=========
Changelog
=========

1.14.0 (2025-02-06)
-------------------

* Support Django 5.2.

1.13.0 (2024-10-27)
-------------------

* Drop Django 3.2 to 4.1 support.

* Drop Python 3.8 support.

* Support Python 3.13.

1.12.0 (2024-06-19)
-------------------

* Support Django 5.1.

1.11.0 (2023-10-11)
-------------------

* Support Django 5.0.

1.10.0 (2023-07-10)
-------------------

* Drop Python 3.7 support.

1.9.0 (2023-06-14)
------------------

* Support Python 3.12.

1.8.0 (2023-02-25)
------------------

* Support Django 4.2.

1.7.0 (2022-06-05)
------------------

* Support Python 3.11.

* Support Django 4.1.

1.6.0 (2022-05-10)
------------------

* Drop support for Django 2.2, 3.0, and 3.1.

1.5.0 (2022-01-10)
------------------

* Drop Python 3.6 support.

1.4.0 (2021-10-05)
------------------

* Support Python 3.10.

1.3.0 (2021-09-28)
------------------

* Support Django 4.0.

1.2.0 (2021-08-13)
------------------

* Add type hints.

* Stop distributing tests to reduce package size. Tests are not intended to be
  run outside of the tox setup in the repository. Repackagers can use GitHub's
  tarballs per tag.

1.1.0 (2021-01-25)
------------------

* Support Django 3.2.

1.0.3 (2021-01-04)
------------------

* Fix construction of PostgreSQL version from its integer form so that e.g.
  ``10.1`` is not parsed as ``10.0.1``.

  `Issue #24 <https://github.com/adamchainz/django-version-checks/issues/24>`__.

1.0.2 (2020-12-16)
------------------

* Remove dependency on wrapt.

1.0.1 (2020-12-14)
------------------

* Fix running on Django 3.1 when ``databases=None``.

1.0.0 (2020-12-14)
------------------

* Initial release.
