#!/usr/bin/env python3
"""
Script to apply macOS compatibility patches to GxPlugins.
This script applies:
1. Makefile changes:
   - Remove -Wl,--gc-sections flag (incompatible with macOS linker)
   - Wrap STRIP commands in Linux conditional
2. Plugin .cpp changes:
   - Add platform-specific __rt_func and __rt_data macros for Apple compatibility

The script only applies changes if the git repository is clean (unmodified).
"""

import os
import re
import sys
import glob
import subprocess
from pathlib import Path


def is_git_clean(repo_path):
    """Check if the repository is in a clean state (no modifications)."""
    try:
        result = subprocess.run(
            ['git', 'status', '--porcelain', '.'],
            cwd=repo_path,
            capture_output=True,
            text=True,
            check=True
        )
        # If output is empty, repo is clean
        return len(result.stdout.strip()) == 0
    except subprocess.CalledProcessError:
        # Not a git repo or git command failed
        return False


def apply_makefile_changes(makefile_path):
    """Apply changes to the Makefile."""
    print(f"Processing Makefile: {makefile_path}")

    with open(makefile_path, 'r') as f:
        content = f.read()

    original_content = content
    changes_made = False

    # Change 1: Remove -Wl,--gc-sections flag (incompatible with macOS)
    if '-Wl,--gc-sections ' in content:
        content = content.replace('-Wl,--gc-sections ', '')
        print("  ✓ Removed -Wl,--gc-sections flag")
        changes_made = True

    # Change 2: Wrap STRIP commands in nogui target with Linux conditional
    nogui_pattern = r'(nogui\s*:.*?\n(?:.*?\n)*?)\t(\$\(STRIP\)[^\n]+)'

    def wrap_strip_in_conditional(match):
        prefix = match.group(1)
        strip_line = match.group(2)

        # Check if already wrapped in conditional
        if 'ifeq' in prefix or 'ifeq' in strip_line:
            return match.group(0)

        indent = '\t'
        return f"{prefix}ifeq ($(TARGET), Linux)\n{indent}{strip_line}\nendif"

    if re.search(r'nogui\s*:', content):
        new_content = re.sub(nogui_pattern, wrap_strip_in_conditional, content)
        if new_content != content:
            content = new_content
            print("  ✓ Wrapped STRIP commands in Linux conditional")
            changes_made = True

    # Write changes if any were made
    if changes_made and content != original_content:
        with open(makefile_path, 'w') as f:
            f.write(content)
        print(f"  ✓ Makefile updated successfully\n")
        return True
    else:
        print(f"  ℹ No changes made to Makefile\n")
        return False


def apply_cpp_changes(cpp_file_path):
    """Apply platform-specific macro changes to .cpp file."""
    print(f"Processing C++ file: {cpp_file_path}")

    with open(cpp_file_path, 'r') as f:
        content = f.read()

    original_content = content
    changes_made = False

    # Pattern to find the macro definitions
    pattern = r'#define\s+__rt_func\s+__attribute__\(\(section\("\.rt\.text"\)\)\)\s*\n#define\s+__rt_data\s+__attribute__\(\(section\("\.rt\.data"\)\)\)'

    if re.search(pattern, content):
        # Replace with platform-specific version
        replacement = '''#ifdef __APPLE__
    #define __rt_func __attribute__((section("__TEXT,__rt_data")))
    #define __rt_data __attribute__((section("__DATA,__rt_data")))
#else
    #define __rt_func __attribute__((section(".rt.text")))
    #define __rt_data __attribute__((section(".rt.data")))
#endif'''

        content = re.sub(pattern, replacement, content)
        print("  ✓ Added platform-specific __rt_func and __rt_data macros")
        changes_made = True

    # Write changes if any were made
    if changes_made and content != original_content:
        with open(cpp_file_path, 'w') as f:
            f.write(content)
        print(f"  ✓ C++ file updated successfully\n")
        return True
    else:
        print(f"  ℹ No changes made to C++ file\n")
        return False


def main():
    if len(sys.argv) < 2:
        print("Usage: python apply_changes.py <target_repository_path>")
        print("\nThis script will:")
        print("  1. Find and update the Makefile")
        print("  2. Find .cpp files in the plugin/ directory and update them")
        sys.exit(1)

    target_repo = Path(sys.argv[1])

    if not target_repo.exists():
        print(f"Error: Directory {target_repo} does not exist")
        sys.exit(1)

    print(f"Applying changes to repository: {target_repo}\n")
    print("=" * 60)

    # Check if git repository is clean
    if not is_git_clean(target_repo):
        print("ℹ Repository has local modifications - skipping (already patched)")
        print("=" * 60)
        print("\nSummary:")
        print("  ℹ Skipped - repository already modified")
        print("\n✓ Done!")
        sys.exit(0)

    changes_summary = []

    # Apply Makefile changes
    makefile_path = target_repo / "Makefile"
    if makefile_path.exists():
        if apply_makefile_changes(makefile_path):
            changes_summary.append("✓ Makefile updated")
        else:
            changes_summary.append("ℹ Makefile - no changes made")
    else:
        print(f"⚠ Makefile not found at {makefile_path}\n")
        changes_summary.append("⚠ Makefile not found")

    # Apply .cpp changes
    plugin_dir = target_repo / "plugin"
    if plugin_dir.exists() and plugin_dir.is_dir():
        cpp_files = list(plugin_dir.glob("*.cpp"))
        if cpp_files:
            print(f"Found {len(cpp_files)} .cpp file(s) in plugin directory")
            for cpp_file in cpp_files:
                if apply_cpp_changes(cpp_file):
                    changes_summary.append(f"✓ {cpp_file.name} updated")
                else:
                    changes_summary.append(f"ℹ {cpp_file.name} - no changes made")
        else:
            print("⚠ No .cpp files found in plugin directory\n")
            changes_summary.append("⚠ No .cpp files found")
    else:
        print(f"⚠ plugin directory not found at {plugin_dir}\n")
        changes_summary.append("⚠ plugin directory not found")

    # Print summary
    print("=" * 60)
    print("\nSummary:")
    for item in changes_summary:
        print(f"  {item}")

    print("\n✓ Done!")


if __name__ == "__main__":
    main()
