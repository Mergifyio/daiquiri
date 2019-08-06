=======================================
daiquiri -- Python logging setup helper
=======================================

.. image:: https://circleci.com/gh/jd/daiquiri.svg?style=svg
   :target: https://circleci.com/gh/jd/daiquiri

.. image:: https://img.shields.io/pypi/v/daiquiri.svg
    :target: https://pypi.python.org/pypi/daiquiri
    :alt: Latest Version

The daiquiri library provides an easy way to configure logging. It also
provides some custom formatters and handlers.

* Free software: Apache license
* Source: https://github.com/jd/daiquiri

Installation
============

  pip install daiquiri

If you want to enable support of JSON output, you must also install the `json`
flavor::

  pip install daiquiri[json]

If you want to enable systemd support, you must install the `systemd` flavor::

  pip install daiquiri[systemd]

Usage
=====

The basic usage of daiquiri is to call the `daiquiri.setup` function that will
setup logging with the options passed as keyword arguments. If no arguments are
passed, the default will log to `stderr`. If `stderr` is a terminal, the output
will use colors.

.. literalinclude:: ../../examples/basic.py

You can specify different outputs with different formatters. The
`daiquiri.output` module provides a collection of `Output` classes that you can
use to your liking to configure the logging output. Any number of output can be
configured.

.. literalinclude:: ../../examples/output.py

If the default output configurations suit your needs, then for convenience you
may pass the name of an output as a string rather than needing to import the
class and produce an instance.

.. literalinclude:: ../../examples/stringnames.py

At the moment the names `'stderr'`, `'stdout'`, `'syslog'`, and `'journal'` are
available, assuming the underlying handler is available.


Picking format
--------------

You can configure the format of any output by passing a formatter as the
`formatter` argument to the contructor. Two default formatters are available:
`daiquiri.formatter.TEXT_FORMATTER` which prints log messages as text, and the
`daiquiri.formatter.JSON_FORMATTER` which prints log messages as parsable JSON
(requires `python-json-logger`).

You can provide any class of type `logging.Formatter` as a formatter.

.. literalinclude:: ../../examples/formatter.py

Python warning support
----------------------

The Python `warnings` module is sometimes used by applications and libraries to
emit warnings. By default, they are printed on `stderr`. Daiquiri overrides
this by default and log warnings to the `py.warnings` logger.

This can be disabled by passing the `capture_warnings=False` argument to
`daiquiri.setup`.

Extra usage
-----------

While it's not mandatory to use `daiquiri.getLogger` to get a logger instead of
`logging.getLogger`, it is recommended as daiquiri provides an enhanced version
of the logger object. It allows any keyword argument to be passed to the
logging method and that will be available as part of the record.

.. literalinclude:: ../../examples/extra.py

Advanced Extra usage
-----------

The enhanced logger object provided by `daiquiri.getLogger` is also capable of
supporting keyword arguments to the logging method without the logger itself
having been configured to expect those specific keywords. This requires the
use of the ExtrasFormatter or the ColorExtrasFormatter classes. The
documentation for the ExtrasFormatter specifies the various options you can
configure on it.

.. literalinclude:: ../../examples/advanced_extra.py


Syslog support
--------------

The `daiquiri.output.Syslog` output provides syslog output.


Systemd journal support
-----------------------

The `daiquiri.output.Journal` output provides systemd journal support. All the
extra arguments passed to the logger will be shipped as extra keys to the
journal.


File support
------------

The `daiquiri.output.File` output class provides support to log into a file.

`daiquiri.output.RotatingFile` class logs to a file that rotates when a
maximum file size has been reached.

`daiquiri.output.TimedRotatingFile` will rotate the log file on a fixed
interval.

.. literalinclude:: ../../examples/files.py

API
===
.. automodule:: daiquiri
   :members:

Output
------
.. automodule:: daiquiri.output
   :members:

Handlers
--------
.. automodule:: daiquiri.handlers
   :members:

Formatter
---------
.. automodule:: daiquiri.formatter
   :members:
