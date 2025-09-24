#!/usr/bin/env python3

import os
import sys

import winrm
from mcp.server.fastmcp import FastMCP


def _import_credentials():
    """Import credentials module with proper error handling."""
    # Add scripts directory to path for shared credentials
    scripts_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
        "scripts",
    )
    if scripts_path not in sys.path:
        sys.path.insert(0, scripts_path)

    try:
        from domain_credentials import (
            get_credentials_from_keychain,
            get_domain_from_hostname,
            test_credentials_available,
        )

        return (
            get_credentials_from_keychain,
            get_domain_from_hostname,
            test_credentials_available,
        )
    except ImportError as e:
        return None, None, None


# Create MCP server
mcp = FastMCP("WinRM Server")

# Add timeout for WinRM operations
WINRM_TIMEOUT = 30


@mcp.tool()
def execute_powershell(hostname: str, command: str) -> dict:
    """Execute PowerShell command on remote Windows host"""

    # Import credentials functions
    (
        get_credentials_from_keychain,
        get_domain_from_hostname,
        test_credentials_available,
    ) = _import_credentials()

    if not all(
        [
            get_credentials_from_keychain,
            get_domain_from_hostname,
            test_credentials_available,
        ]
    ):
        return {
            "error": "Credentials module not available",
            "help": "Ensure domain_credentials module is available in ~/.aws/amazonq/scripts/",
        }

    # Check if credentials are available
    if not test_credentials_available(hostname):
        domain = get_domain_from_hostname(hostname)
        return {
            "error": f"No credentials found for {domain}",
            "help": f"Run 'python3 ~/.aws/amazonq/scripts/domain_auth.py {domain}' to authenticate first",
        }

    try:
        # Get credentials (triggers TouchID)
        username, password = get_credentials_from_keychain(
            get_domain_from_hostname(hostname)
        )

        # Try HTTP first (most Windows servers use HTTP WinRM)
        session = winrm.Session(
            f"http://{hostname}:5985/wsman",
            auth=(username, password),
            transport="ntlm",
            operation_timeout_sec=20,
            read_timeout_sec=25,
        )

        result = session.run_ps(command)

        # Clear password from memory immediately
        password = None

        return {
            "status": result.status_code,
            "stdout": result.std_out.decode("utf-8"),
            "stderr": result.std_err.decode("utf-8"),
        }

    except Exception as e:
        # Clear password from memory on error
        password = None
        return {"error": "WinRM connection or authentication failed"}


@mcp.tool()
def get_system_info(hostname: str) -> dict:
    """Get basic system information from Windows host"""
    command = "Get-ComputerInfo | Select-Object WindowsProductName, TotalPhysicalMemory, CsProcessors | ConvertTo-Json -Compress"
    return execute_powershell(hostname, command)


@mcp.tool()
def get_running_services(hostname: str) -> dict:
    """Get running services from Windows host"""
    command = "Get-Service | Where-Object {$_.Status -eq 'Running'} | Select-Object Name, Status, StartType | Sort-Object Name | ConvertTo-Json -Compress"
    return execute_powershell(hostname, command)


@mcp.tool()
def get_disk_space(hostname: str) -> dict:
    """Get disk space information from Windows host"""
    command = "Get-WmiObject -Class Win32_LogicalDisk | Select-Object DeviceID, @{Name='Size(GB)';Expression={[math]::Round($_.Size/1GB,2)}}, @{Name='FreeSpace(GB)';Expression={[math]::Round($_.FreeSpace/1GB,2)}} | ConvertTo-Json -Compress"
    return execute_powershell(hostname, command)


def main():
    """Main entry point for the WinRM MCP server."""
    import asyncio

    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
