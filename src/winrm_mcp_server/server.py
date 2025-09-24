#!/usr/bin/env python3

import os
import sys

import winrm
from mcp.server.fastmcp import FastMCP

from .credentials import get_credentials, test_credentials_available

# Create MCP server
mcp = FastMCP("WinRM Server")

# Add timeout for WinRM operations
WINRM_TIMEOUT = 30


@mcp.tool()
def execute_powershell(hostname: str, command: str) -> dict:
    """Execute PowerShell command on remote Windows host"""

    # Check if credentials are available (non-interactive check)
    if not test_credentials_available(hostname):
        return {
            "error": "No cached credentials available",
            "help": "Run winrm-mcp-server in interactive mode first to authenticate",
        }

    try:
        # Get credentials (may prompt if not cached)
        username, password = get_credentials(hostname)

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
        return {"error": f"WinRM connection or authentication failed: {str(e)}"}


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


@mcp.tool()
def setup_credentials(hostname: str) -> dict:
    """Setup credentials for a Windows host (interactive)"""
    try:
        username, password = get_credentials(hostname)
        # Clear password from memory immediately
        password = None
        return {
            "status": "success",
            "message": f"Credentials configured for {username}",
        }
    except Exception as e:
        return {"error": f"Failed to setup credentials: {str(e)}"}


def main():
    """Main entry point for the WinRM MCP server."""
    import asyncio

    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
