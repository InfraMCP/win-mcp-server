# WinRM MCP Server

A Model Context Protocol (MCP) server that provides AI agents with the ability to interact with Windows servers using Windows Remote Management (WinRM). This server enables secure remote PowerShell execution and system management tasks on Windows hosts.

## Features

- **Secure Authentication**: Uses domain credentials stored in macOS Keychain with TouchID authentication
- **PowerShell Execution**: Execute arbitrary PowerShell commands on remote Windows hosts
- **System Information**: Get basic system information, running services, and disk space
- **Error Handling**: Comprehensive error handling with helpful error messages
- **Memory Safety**: Credentials are cleared from memory immediately after use

## Installation

```bash
pip install winrm-mcp-server
```

## Configuration

### Prerequisites

1. **Domain Authentication**: Set up domain credentials using the authentication script:
   ```bash
   python3 ~/.aws/amazonq/scripts/domain_auth.py domain.local
   python3 ~/.aws/amazonq/scripts/domain_auth.py company.local
   ```

2. **WinRM Configuration**: Ensure target Windows hosts have WinRM enabled and configured.

### MCP Configuration

Add to your MCP settings file (e.g., `~/.config/mcp/settings.json`):

```json
{
  "mcpServers": {
    "winrm": {
      "command": "winrm-mcp-server"
    }
  }
}
```

## Available Tools

### `execute_powershell(hostname: str, command: str)`
Execute arbitrary PowerShell commands on a remote Windows host.

**Parameters:**
- `hostname`: The target Windows hostname (FQDN)
- `command`: PowerShell command to execute

**Returns:**
- `status`: Exit code of the command
- `stdout`: Standard output from the command
- `stderr`: Standard error from the command

### `get_system_info(hostname: str)`
Get basic system information from a Windows host.

**Returns:** JSON with Windows product name, total physical memory, and processor information.

### `get_running_services(hostname: str)`
Get list of running services from a Windows host.

**Returns:** JSON array of running services with name, status, and start type.

### `get_disk_space(hostname: str)`
Get disk space information from a Windows host.

**Returns:** JSON array of logical disks with device ID, total size, and free space in GB.

## Usage Examples

### Basic System Check
```bash
"Get system info and disk space for server01.domain.local"
```

### Service Management
```bash
"Check if IIS is running on webserver.domain.local"
"Get running services on server01.domain.local"
```

### Custom PowerShell Commands
```bash
"Run 'Get-EventLog -LogName System -Newest 10' on server01.domain.local"
"Execute 'Get-Process | Sort-Object CPU -Descending | Select-Object -First 10' on server01.domain.local"
```

## Security

- **Credential Storage**: Domain credentials are securely stored in macOS Keychain
- **TouchID Authentication**: Credentials require TouchID authentication for access
- **Memory Safety**: Passwords are immediately cleared from memory after use
- **Transport Security**: Uses NTLM authentication over HTTP (configurable for HTTPS)

## Development

### Setup Development Environment

```bash
git clone https://github.com/rorymcmahon/winrm-mcp-server.git
cd winrm-mcp-server
pip install -e ".[dev]"
```

### Running Tests

```bash
pytest
```

### Code Formatting

```bash
black src/
isort src/
```

## Requirements

- Python 3.8+
- macOS (for Keychain integration)
- Domain credentials configured via authentication script
- Target Windows hosts with WinRM enabled

## License

MIT License - see [LICENSE](LICENSE) file for details.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## Support

For issues and questions:
- [GitHub Issues](https://github.com/rorymcmahon/winrm-mcp-server/issues)
- [Documentation](https://github.com/rorymcmahon/winrm-mcp-server#readme)
