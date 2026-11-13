# Security Policy

This policy covers the `daiquiri` package published on PyPI and the code in
this repository.

## Reporting a vulnerability

Please do not report security vulnerabilities through public GitHub issues,
discussions or pull requests.

Report them privately through Mergify's bug bounty program on HackerOne:
<https://hackerone.com/mergify>. For other security questions, write to
<security@mergify.com>.

A useful report says which daiquiri and Python versions you ran
(`pip show daiquiri`, `python --version`), how to reproduce the issue and
what an attacker gains from it.

Mergify's vulnerability disclosure policy is published at
<https://docs.mergify.com/security/#vulnerability-disclosure>.

## Supported versions

Security fixes ship in a new release of daiquiri on PyPI; only the latest
release is supported. Upgrade with `pip install --upgrade daiquiri`.
