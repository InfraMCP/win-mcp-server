#!/usr/bin/env python3
"""
Generate comprehensive dependency report for supply chain security analysis.
"""

import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path


def run_command(cmd):
    """Run command and return output."""
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, check=True)
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"Error running command '{cmd}': {e}")
        return None


def get_package_info(package_name):
    """Get detailed package information."""
    cmd = f"pip3 show {package_name}"
    output = run_command(cmd)
    if not output:
        return None
    
    info = {}
    for line in output.split('\n'):
        if ':' in line:
            key, value = line.split(':', 1)
            info[key.strip()] = value.strip()
    return info


def get_dependency_tree():
    """Get full dependency tree."""
    cmd = "pip3 list --format=json"
    output = run_command(cmd)
    if not output:
        return []
    
    try:
        return json.loads(output)
    except json.JSONDecodeError:
        return []


def generate_report():
    """Generate comprehensive dependency report."""
    print("Generating dependency security report...")
    
    # Core dependencies from requirements.txt
    core_deps = ["mcp", "pywinrm"]
    
    report = {
        "generated_at": datetime.now().isoformat(),
        "python_version": sys.version,
        "core_dependencies": {},
        "all_dependencies": [],
        "security_notes": []
    }
    
    # Get detailed info for core dependencies
    for dep in core_deps:
        info = get_package_info(dep)
        if info:
            report["core_dependencies"][dep] = {
                "version": info.get("Version", "unknown"),
                "summary": info.get("Summary", ""),
                "home_page": info.get("Home-page", ""),
                "author": info.get("Author", ""),
                "license": info.get("License", ""),
                "requires": info.get("Requires", "").split(", ") if info.get("Requires") else []
            }
    
    # Get all installed packages
    all_packages = get_dependency_tree()
    report["all_dependencies"] = all_packages
    
    # Add security recommendations
    report["security_notes"] = [
        "Review this report when security vulnerabilities are announced",
        "Update dependencies regularly but test thoroughly",
        "Monitor security advisories for listed packages",
        "Consider using tools like safety or pip-audit for vulnerability scanning"
    ]
    
    return report


def main():
    """Main function."""
    report = generate_report()
    
    # Write JSON report
    report_path = Path("docs/dependency-report.json")
    report_path.parent.mkdir(exist_ok=True)
    
    with open(report_path, 'w') as f:
        json.dump(report, f, indent=2)
    
    # Write human-readable markdown
    md_path = Path("docs/DEPENDENCIES.md")
    with open(md_path, 'w') as f:
        f.write("# Dependency Security Report\n\n")
        f.write(f"Generated: {report['generated_at']}\n\n")
        
        f.write("## Core Dependencies\n\n")
        for name, info in report["core_dependencies"].items():
            f.write(f"### {name} v{info['version']}\n")
            f.write(f"- **Summary**: {info['summary']}\n")
            f.write(f"- **License**: {info['license']}\n")
            f.write(f"- **Homepage**: {info['home_page']}\n")
            if info['requires']:
                f.write(f"- **Dependencies**: {', '.join(info['requires'])}\n")
            f.write("\n")
        
        f.write("## Security Guidelines\n\n")
        for note in report["security_notes"]:
            f.write(f"- {note}\n")
        
        f.write(f"\n## All Installed Packages ({len(report['all_dependencies'])} total)\n\n")
        f.write("| Package | Version |\n")
        f.write("|---------|----------|\n")
        for pkg in sorted(report["all_dependencies"], key=lambda x: x["name"]):
            f.write(f"| {pkg['name']} | {pkg['version']} |\n")
    
    print(f"Dependency report generated:")
    print(f"- JSON: {report_path}")
    print(f"- Markdown: {md_path}")


if __name__ == "__main__":
    main()
