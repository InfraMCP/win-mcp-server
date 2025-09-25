# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
