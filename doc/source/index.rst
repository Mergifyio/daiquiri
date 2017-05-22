=======================================
daiquiri -- Python logging setup helper
=======================================

.. image:: https://travis-ci.org/jd/daiquiri.png?branch=master
    :target: https://travis-ci.org/jd/daiquiri
    :alt: Build Status

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

Usage
=====

The basic usage of daiquiri is to call the `setup` function that will setup
logging with the options passed as keyword arguments. If no argument are
passed, the default will log to `stderr`.

.. literalinclude:: ../../examples/basic.py

You can specify different outputs with different formatters. The
`daiquiri.output` module provides a collection of `Output` classes that you can
use to your liking to configut the logging output. Any number of output can bex
configured.

.. literalinclude:: ../../examples/output.py


Picking format
--------------

You can configure the format of any output by passing a formatter to as the
`formatter` argument to the contructor. Two default formatter are available:
`daiquiri.formatter.TEXT_FORMATTER` which prints log messages as text, and the
`daiquiri.formatter.JSON_FORMATTER` which prints log messages as parsable JSON.

You can provide any class of type `logging.Formatter` as a formatter.

.. literalinclude:: ../../examples/formatter.py

Extra usage
-----------

While it's not mandatory to use `daiquiri.getLogger` to get a logger instead of
`logging.getLogger`, it is recommended as daiquiri provides an enhanced version
of the logger object. It allows any keyword argument to be passed to the
logging method and that will be available as part of the record.

.. literalinclude:: ../../examples/extra.py


Syslog support
--------------

The `daiquiri.output.Syslog` output provides syslog output.


Systemd journal support
-----------------------

The `daiquiri.output.Journal` output provides systemd journal support. All the
extra argument passed to the logger will be shipped as extra keys to the
journal.


File support
------------

The `daiquiri.output.File` output class provides support to log into a file.
