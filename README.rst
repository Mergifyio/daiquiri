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
logging with the options passed as keyword arguments.

.. literalinclude:: examples/basic.py

While it's not mandatory to use `daiquiri.getLogger` to get a logger instead of
`logging.getLogger`, it is recommended as daiquiri provides an enhanced version
of the logger. It allows any keyword argument to be passed to the logging
method and that will be available as part of the record.


Syslog support
--------------
By passing `use_syslog=True` to `daiquiri.setup`, all messages will be logged
to syslog.

Systemd journal support
-----------------------
By passing `use_journal=True` to `daiquiri.setup`, all messages will be logged
to systemd journal. All the extra parameters passed to the logging methods will
be sent as extra keys to the logging information.
