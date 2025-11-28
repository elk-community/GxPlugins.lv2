#!/usr/bin/env python3
"""
Post-build script for macOS LV2 plugin builds.
Fixes the missing .dylib extension issue on macOS builds.
"""

import os
import sys
import shutil
import glob
import re


def find_binary_without_extension(directory):
    """Find binary files with no extension (ending with just a dot)."""
    pattern = os.path.join(directory, "*.")
    matches = glob.glob(pattern)
    return matches


def get_basename_without_extension(filepath):
    """Get the basename of a file, removing trailing dot if present."""
    basename = os.path.basename(filepath)
    if basename.endswith('.'):
        basename = basename[:-1]
    return basename


def create_lv2_bundle(binary_path, mod_dir="MOD"):
    """
    Create LV2 bundle directory structure.

    Args:
        binary_path: Path to the binary file (with or without extension)
        mod_dir: Directory containing TTL files and modgui folder
    """
    # Get the basename without extension (for the dylib name)
    basename = get_basename_without_extension(binary_path)

    # Use the parent directory name as the bundle directory name
    # This will be something like GxAxisFace.lv2
    parent_dir = os.path.basename(os.getcwd())
    bundle_dir = parent_dir if parent_dir.endswith('.lv2') else f"{parent_dir}.lv2"

    print(f"Creating LV2 bundle: {bundle_dir}")

    # Create the bundle directory
    os.makedirs(bundle_dir, exist_ok=True)

    # Move and rename the binary to .dylib
    dylib_name = f"{basename}.dylib"
    target_binary = os.path.join(bundle_dir, dylib_name)

    print(f"Moving {binary_path} -> {target_binary}")
    shutil.move(binary_path, target_binary)

    # Copy all files from MOD directory
    if os.path.exists(mod_dir):
        print(f"Copying files from {mod_dir}/ to {bundle_dir}/")

        for item in os.listdir(mod_dir):
            src = os.path.join(mod_dir, item)
            dst = os.path.join(bundle_dir, item)

            if os.path.isdir(src):
                if os.path.exists(dst):
                    shutil.rmtree(dst)
                shutil.copytree(src, dst)
                print(f"  Copied directory: {item}")
            else:
                shutil.copy2(src, dst)
                print(f"  Copied file: {item}")
    else:
        print(f"Warning: MOD directory '{mod_dir}' not found")
        return False

    # Modify manifest.ttl to reference .dylib instead of .so
    manifest_path = os.path.join(bundle_dir, "manifest.ttl")

    if os.path.exists(manifest_path):
        print(f"Updating {manifest_path}")

        with open(manifest_path, 'r') as f:
            content = f.read()

        # Replace .so with .dylib in the lv2:binary line
        # Pattern matches: <basename.so> and replaces with <basename.dylib>
        pattern = rf'(<{basename}\.so>)'
        replacement = f'<{dylib_name}>'

        modified_content = re.sub(pattern, replacement, content)

        if modified_content != content:
            with open(manifest_path, 'w') as f:
                f.write(modified_content)
            print(f"  Updated lv2:binary reference: {basename}.so -> {dylib_name}")
        else:
            print(f"  Warning: Could not find '{basename}.so' reference in manifest.ttl")
    else:
        print(f"Warning: manifest.ttl not found at {manifest_path}")
        return False

    print(f"\nSuccess! Bundle created at: {bundle_dir}")
    return True


def main():
    # Get current directory
    current_dir = os.getcwd()

    print("macOS LV2 Post-Build Script")
    print("=" * 50)
    print(f"Working directory: {current_dir}\n")

    # Find binary files without extension
    binaries = find_binary_without_extension(current_dir)

    if not binaries:
        print("Error: No binary files with missing extension found")
        print("Looking for files matching pattern: *.")
        sys.exit(1)

    if len(binaries) > 1:
        print(f"Warning: Found multiple binary files: {binaries}")
        print("Processing all of them...\n")

    # Process each binary found
    success = True
    for binary in binaries:
        print(f"\nProcessing: {binary}")
        if not create_lv2_bundle(binary):
            success = False

    if success:
        print("\n" + "=" * 50)
        print("All bundles created successfully!")
        sys.exit(0)
    else:
        print("\n" + "=" * 50)
        print("Some errors occurred during bundle creation")
        sys.exit(1)


if __name__ == "__main__":
    main()
