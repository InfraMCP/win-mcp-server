# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.3.0] - 2026-10-22

### Added
- Read WinRM credentials from `WINRM_USER`/`WINRM_PWD` (or `WINRM-USER`/`WINRM-PWD`)
  environment variables, bypassing the GUI prompt and Keychain cache for
  non-interactive/CI usage.
- Test suite for credential resolution (`tests/test_credentials.py`) and a
  `Tests` CI workflow that runs it on Python 3.10-3.12.
- `pip-audit` job in the security workflow that scans the full resolved
  dependency tree (runtime + dev + transitive), not just the runtime pins.

### Fixed
- Cached credential lookup now enumerates **all** `win-mcp` Keychain entries via
  `security dump-keychain` instead of `find-generic-password` (which returns only
  one), so the correct credentials are found when multiple hosts are stored.
- IP-address hosts are keyed on the full address (e.g. `10.211.55.7`) instead of
  being mangled by FQDN splitting, and the 4-hour TTL is now enforced on read.
- Corrected `requires-python` to `>=3.10` (and dropped the 3.8/3.9 classifiers):
  the `mcp` dependency requires 3.10+, so the previous `>=3.8` claim was
  unsatisfiable and would install then fail at import on 3.8/3.9.

### Changed
- Bumped `mcp` from 1.14.1 to 1.30.0, `pytest` to 9.0.3, `pytest-asyncio` to
  1.4.0, and `black` to 26.3.1 (resolves all open Dependabot alerts).

## [0.2.3] - 2025-09-25

### Changed
- Updated README with correct Python version requirements (3.10+)
- Added status badges for automated quality checks (Pylint, Safety, Dependency Security)

## [0.2.2] - 2025-09-24

### Fixed
- Improved code quality with perfect pylint score (10.00/10)
- Fixed broad exception handling with specific exception types
- Added comprehensive module docstrings

### Added
- Security workflows for dependency scanning
- Automated vulnerability detection with Safety and pip-audit
- PR commenting for security findings

## [0.2.1] - 2025-09-18

### Added
- Enhanced error handling and logging
- Improved WinRM connection management
- Better credential validation

## [0.2.0] - 2025-09-15

### Added
- Windows Remote Management (WinRM) support
- PowerShell command execution on remote Windows hosts
- System information retrieval tools
- Secure domain credential management with macOS Keychain
- TouchID authentication for credential access

### Security
- Secure credential storage using macOS Keychain
- Domain authentication support
- Encrypted credential transmission
