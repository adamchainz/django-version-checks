=======
History
=======

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
