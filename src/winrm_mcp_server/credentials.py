#!/usr/bin/env python3
"""Secure credential management for WinRM connections."""

import getpass
import os
import subprocess
import sys
import time
from typing import Optional, Tuple


def get_domain_from_hostname(hostname: str) -> str:
    """Extract domain from FQDN or prompt user."""
    parts = hostname.split(".")
    if len(parts) > 1:
        # Extract domain from FQDN (e.g., server.domain.local -> domain.local)
        domain = ".".join(parts[1:])
        return domain

    # Fallback: prompt user
    suggested_domain = f"{hostname}.local"
    domain = input(f"Enter domain for {hostname} [{suggested_domain}]: ").strip()
    return domain if domain else suggested_domain


def get_username_suggestion() -> str:
    """Get suggested username (current user)."""
    return getpass.getuser()


def keychain_get_password(service: str, account: str) -> Optional[str]:
    """Get password from macOS Keychain."""
    try:
        result = subprocess.run(
            ["security", "find-generic-password", "-s", service, "-a", account, "-w"],
            capture_output=True,
            text=True,
            check=True,
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError:
        return None


def keychain_set_password(
    service: str, account: str, password: str, ttl_hours: int = 4
):
    """Store password in macOS Keychain with TTL."""
    # Delete existing entry if present
    subprocess.run(
        ["security", "delete-generic-password", "-s", service, "-a", account],
        capture_output=True,
    )

    # Add new entry with comment containing expiration time
    expiry_time = int(time.time()) + (ttl_hours * 3600)

    subprocess.run(
        [
            "security",
            "add-generic-password",
            "-s",
            service,
            "-a",
            account,
            "-w",
            password,
            "-j",
            f"expires:{expiry_time}",
        ],
        check=True,
    )


def keychain_check_expired(service: str, account: str) -> bool:
    """Check if keychain entry is expired."""
    try:
        result = subprocess.run(
            ["security", "find-generic-password", "-s", service, "-a", account, "-j"],
            capture_output=True,
            text=True,
            check=True,
        )

        # Parse comment for expiry time
        comment = result.stdout.strip()
        if comment.startswith("expires:"):
            expiry_time = int(comment.split(":")[1])
            return time.time() > expiry_time
    except (subprocess.CalledProcessError, ValueError, IndexError):
        pass

    return True  # Assume expired if we can't determine


def get_credentials(hostname: str) -> Tuple[str, str]:
    """Get credentials for hostname with secure prompting and caching."""
    domain = get_domain_from_hostname(hostname)
    service = f"winrm-mcp-{domain}"

    # Get username
    suggested_username = get_username_suggestion()
    username = input(f"Username for {domain} [{suggested_username}]: ").strip()
    if not username:
        username = suggested_username

    account = f"{domain}\\{username}"

    # Check for cached password
    if not keychain_check_expired(service, account):
        password = keychain_get_password(service, account)
        if password:
            print(f"Using cached credentials for {account}")
            return username, password

    # Prompt for password securely
    password = getpass.getpass(f"Password for {account}: ")
    if not password:
        print("Password cannot be empty", file=sys.stderr)
        sys.exit(1)

    # Store in keychain with 4-hour TTL
    try:
        keychain_set_password(service, account, password)
        print(f"Credentials cached for 4 hours")
    except subprocess.CalledProcessError as e:
        print(f"Warning: Could not cache credentials: {e}", file=sys.stderr)

    return username, password


def test_credentials_available(hostname: str) -> bool:
    """Test if valid credentials are available for hostname."""
    domain = get_domain_from_hostname(hostname)
    service = f"winrm-mcp-{domain}"
    suggested_username = get_username_suggestion()
    account = f"{domain}\\{suggested_username}"

    if keychain_check_expired(service, account):
        return False

    return keychain_get_password(service, account) is not None
