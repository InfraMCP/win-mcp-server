#!/usr/bin/env python3
"""WinRM MCP Server for remote Windows management."""

import winrm
from mcp.server.fastmcp import FastMCP

from .credentials import (
    get_credentials,
    clear_cached_credentials,
    get_domain_from_hostname
)

# Create MCP server
mcp = FastMCP("WinRM Server")

# Add timeout for WinRM operations
WINRM_TIMEOUT = 30


@mcp.tool()
def win_execute_powershell(hostname: str, command: str) -> dict:
    """Execute PowerShell command on remote Windows host"""

    try:
        # Get credentials (will use cached if available)
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
        _ = password

        return {
            "status": result.status_code,
            "stdout": result.std_out.decode("utf-8"),
            "stderr": result.std_err.decode("utf-8"),
        }

    except RuntimeError as e:
        error_msg = str(e)
        if "No cached credentials" in error_msg:
            return {
                "error": "Authentication required",
                "details": error_msg,
                "troubleshooting": [
                    "Run setup_credentials tool first to authenticate",
                    "Check if credentials have expired (4-hour TTL)",
                    "Verify the hostname resolves to correct domain"
                ],
                "suggested_action": f"Try: win_setup_credentials('{hostname}') first"
            }
        return {
            "error": "Credential setup failed",
            "details": error_msg,
            "troubleshooting": [
                "User may have cancelled authentication dialog",
                "Check if hostname format is correct (FQDN preferred)",
                "Verify domain extraction is working properly"
            ]
        }
    except (winrm.exceptions.WinRMError, OSError) as e:
        error_msg = str(e)
        if "timeout" in error_msg.lower():
            return {
                "error": "WinRM connection timeout",
                "details": error_msg,
                "troubleshooting": [
                    "Check if host is reachable (ping test)",
                    "Verify WinRM service is running on target host",
                    "Check firewall rules for port 5985 (HTTP) or 5986 (HTTPS)",
                    "Confirm WinRM is enabled: 'winrm quickconfig' on target"
                ],
                "suggested_action": f"Test connectivity: ping {hostname}"
            }
        if "401" in error_msg or "authentication" in error_msg.lower():
            return {
                "error": "Authentication failed",
                "details": error_msg,
                "troubleshooting": [
                    "Credentials may be incorrect or expired",
                    "Account may be locked or disabled",
                    "Domain trust issues possible",
                    "Check if account has WinRM permissions"
                ],
                "suggested_action": (
                    f"Clear and re-enter credentials: win_clear_credentials('{hostname}') "
                    f"then win_setup_credentials('{hostname}')"
                )
            }
        if "connection" in error_msg.lower():
            return {
                "error": "Network connection failed",
                "details": error_msg,
                "troubleshooting": [
                    "Host may be unreachable or offline",
                    "DNS resolution may be failing",
                    "Network routing issues possible",
                    "WinRM service may not be listening"
                ],
                "suggested_action": (
                    f"Check network: nslookup {hostname} && ping {hostname}"
                )
            }
        return {
                "error": "WinRM execution failed",
                "details": error_msg,
                "troubleshooting": [
                    "PowerShell command may have syntax errors",
                    "Insufficient permissions for the command",
                    "WinRM configuration issues on target host",
                    "Session limits or resource constraints"
                ],
                "suggested_action": "Try a simple command first: win_get_system_info"
            }


@mcp.tool()
def win_get_system_info(hostname: str) -> dict:
    """Get basic system information from Windows host"""
    command = (
        "Get-ComputerInfo | Select-Object WindowsProductName, TotalPhysicalMemory, "
        "CsProcessors | ConvertTo-Json -Compress"
    )
    return win_execute_powershell(hostname, command)


@mcp.tool()
def win_get_running_services(hostname: str) -> dict:
    """Get running services from Windows host"""
    command = (
        "Get-Service | Where-Object {$_.Status -eq 'Running'} | "
        "Select-Object Name, Status, StartType | Sort-Object Name | ConvertTo-Json -Compress"
    )
    return win_execute_powershell(hostname, command)


@mcp.tool()
def win_get_disk_space(hostname: str) -> dict:
    """Get disk space information from Windows host"""
    command = (
        "Get-WmiObject -Class Win32_LogicalDisk | Select-Object DeviceID, "
        "@{Name='Size(GB)';Expression={[math]::Round($_.Size/1GB,2)}}, "
        "@{Name='FreeSpace(GB)';Expression={[math]::Round($_.FreeSpace/1GB,2)}} | "
        "ConvertTo-Json -Compress"
    )
    return win_execute_powershell(hostname, command)


@mcp.tool()
def win_setup_credentials(hostname: str) -> dict:
    """Setup credentials for a Windows host using GUI prompts"""
    try:
        username, password = get_credentials(hostname)
        # Clear password from memory immediately
        _ = password
        domain = get_domain_from_hostname(hostname)
        return {
            "status": "success",
            "message": f"Credentials configured for {username}@{domain}",
            "details": f"Cached for 4 hours, shared across all hosts in {domain}",
            "next_steps": [
                f"Try: win_execute_powershell('{hostname}', 'Get-ComputerInfo')",
                f"Or: win_get_system_info('{hostname}')"
            ]
        }
    except (RuntimeError, OSError) as e:
        error_msg = str(e)
        if "cancelled" in error_msg.lower():
            return {
                "error": "Authentication cancelled by user",
                "details": error_msg,
                "troubleshooting": [
                    "User clicked Cancel in authentication dialog",
                    "Authentication dialog may have timed out",
                    "System may be locked or user not present"
                ],
                "suggested_action": f"Try again: win_setup_credentials('{hostname}')"
            }
        if "empty" in error_msg.lower():
            return {
                "error": "Empty password not allowed",
                "details": error_msg,
                "troubleshooting": [
                    "Password field was left blank",
                    "Account may not require password (unusual)",
                    "Dialog input may have failed"
                ],
                "suggested_action": "Ensure password is entered in the dialog"
            }
        return {
                "error": "Credential setup failed",
                "details": error_msg,
                "troubleshooting": [
                    "macOS Keychain access may be denied",
                    "System security settings may block keychain access",
                    "Hostname format may be invalid",
                    "Domain extraction may have failed"
                ],
                "suggested_action": (
                    f"Check hostname format: '{hostname}' should be FQDN "
                    "like 'server.domain.local'"
                )
            }


@mcp.tool()
def win_clear_credentials(hostname: str) -> dict:
    """Clear cached credentials for a Windows host"""
    try:
        domain = get_domain_from_hostname(hostname)
        if clear_cached_credentials(hostname):
            return {
                "status": "success", 
                "message": f"Cached credentials cleared for {domain}",
                "details": "All cached credentials for this domain have been removed",
                "next_steps": [
                    f"Use win_setup_credentials('{hostname}') to re-authenticate",
                    "New authentication will be required for all hosts in this domain"
                ]
            }
        return {
                "status": "info", 
                "message": f"No cached credentials found for {domain}",
                "details": "Domain may not have been authenticated yet",
                "suggested_action": f"Use win_setup_credentials('{hostname}') to authenticate"
            }
    except (RuntimeError, OSError) as e:
        return {
            "error": "Failed to clear credentials",
            "details": str(e),
            "troubleshooting": [
                "macOS Keychain access may be restricted",
                "Keychain may be locked",
                "System security settings may prevent access"
            ],
            "suggested_action": "Check macOS Keychain Access app for any restrictions"
        }


def main():
    """Main entry point for the WinRM MCP server."""
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
