#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TOP_LEVEL="$(dirname "$SCRIPT_DIR")"
PAWPAW_REPO_DIR="$TOP_LEVEL/pawpaw"
BUILD_OUTPUT_DIR="$SCRIPT_DIR/macos-build"
APPLY_CHANGES_SCRIPT="$SCRIPT_DIR/apply_changes.py"
POSTBUILD_SCRIPT="$SCRIPT_DIR/postbuild_macos.py"

# Handle clean option
if [ "$1" = "clean" ]; then
    echo "========================================"
    echo "Cleaning Build Artifacts"
    echo "========================================"
    echo ""

    # Step 1: Run make clean in all Gx* directories
    echo "Running make clean in all plugin directories..."
    for plugin_dir in "$SCRIPT_DIR"/Gx*; do
        if [ -d "$plugin_dir" ] && [ -f "$plugin_dir/Makefile" ]; then
            plugin_name=$(basename "$plugin_dir")
            echo "  Cleaning $plugin_name..."
            (cd "$plugin_dir" && make clean 2>/dev/null) || echo "    (no clean target or already clean)"
        fi
    done

    # Step 2: Reset each Gx* directory individually
    echo ""
    echo "Resetting Gx* plugin directories..."
    for plugin_dir in "$SCRIPT_DIR"/Gx*; do
        if [ -d "$plugin_dir" ]; then
            plugin_name=$(basename "$plugin_dir")
            echo "  Resetting $plugin_name..."
            (cd "$plugin_dir" && git reset --hard HEAD && git clean -fd)
        fi
    done

    # Step 3: Remove output directory
    echo ""
    if [ -d "$BUILD_OUTPUT_DIR" ]; then
        echo "Removing output directory: $BUILD_OUTPUT_DIR"
        rm -rf "$BUILD_OUTPUT_DIR"
        echo "✓ Output directory removed"
    else
        echo "ℹ Output directory does not exist: $BUILD_OUTPUT_DIR"
    fi

    echo ""
    echo "========================================"
    echo "Clean Complete!"
    echo "========================================"
    exit 0
fi

# Check if architecture argument is provided
if [ $# -eq 0 ]; then
    echo "Usage: $0 <architecture>"
    echo "       $0 clean"
    echo ""
    echo "Examples:"
    echo "  $0 macos-universal-10.15    # Build all plugins"
    echo "  $0 clean                     # Clean all build artifacts"
    exit 1
fi

ARCH_ARG="$1"

echo "========================================"
echo "GxPlugins macOS Headless Build Script"
echo "========================================"
echo "Architecture: $ARCH_ARG"
echo "Script directory: $SCRIPT_DIR"
echo "Top level: $TOP_LEVEL"
echo "PawPaw directory: $PAWPAW_REPO_DIR"
echo "Build output: $BUILD_OUTPUT_DIR"
echo ""
echo "DEBUG: Checking if PawPaw directory exists..."
if [ -d "$PAWPAW_REPO_DIR" ]; then
    echo "✓ PawPaw directory found at: $PAWPAW_REPO_DIR"
    if [ -f "$PAWPAW_REPO_DIR/local.env" ]; then
        echo "✓ local.env found"
    else
        echo "✗ local.env NOT found in $PAWPAW_REPO_DIR"
        exit 1
    fi
else
    echo "✗ PawPaw directory NOT found at: $PAWPAW_REPO_DIR"
    exit 1
fi
echo ""

# Step 0: Create macos-build directory
echo "Creating build output directory..."
mkdir -p "$BUILD_OUTPUT_DIR"

# Step 1: Iterate over all Gx* subdirectories
for plugin_dir in "$SCRIPT_DIR"/Gx*; do
    if [ ! -d "$plugin_dir" ]; then
        continue
    fi

    # Save the absolute plugin directory path BEFORE sourcing anything
    # This prevents the path from being affected by environment changes
    PLUGIN_BUILD_DIR="$(cd "$plugin_dir" && pwd)"
    plugin_name=$(basename "$PLUGIN_BUILD_DIR")

    # Ensure we're in the script directory at the start of each iteration
    cd "$SCRIPT_DIR" || { echo "Error: Cannot cd to $SCRIPT_DIR"; exit 1; }

    echo ""
    echo "========================================"
    echo "Building: $plugin_name"
    echo "========================================"
    echo "Plugin directory: $PLUGIN_BUILD_DIR"

    # Step 2: Apply changes to the plugin directory
    echo "Step 1: Applying macOS compatibility patches..."
    "$APPLY_CHANGES_SCRIPT" "$PLUGIN_BUILD_DIR"

    # Ensure we're back in script directory after apply_changes
    cd "$SCRIPT_DIR" || { echo "Error: Cannot cd to $SCRIPT_DIR after apply_changes"; exit 1; }

    # Step 3: Source PawPaw environment
    echo "Step 2: Sourcing PawPaw environment..."
    echo "Current directory: $(pwd)"
    echo "Changing to: $PAWPAW_REPO_DIR"
    cd "$PAWPAW_REPO_DIR" || { echo "Error: Cannot cd to $PAWPAW_REPO_DIR"; exit 1; }
    echo "Now in: $(pwd)"
    source ./local.env "$ARCH_ARG"

    # Step 4: Return to plugin directory (use saved absolute path)
    echo "Step 3: Entering plugin directory: $PLUGIN_BUILD_DIR"
    cd "$PLUGIN_BUILD_DIR" || { echo "Error: Cannot cd to $PLUGIN_BUILD_DIR"; exit 1; }

    # Step 5: Build with make nogui
    echo "Step 4: Building plugin (make nogui)..."
    make nogui

    # Step 6: Run postbuild script
    echo "Step 5: Running post-build packaging..."
    "$POSTBUILD_SCRIPT"

    # Step 7: Move the .lv2 bundle to macos-build
    echo "Step 6: Moving bundle to output directory..."
    for bundle in *.lv2; do
        if [ -d "$bundle" ]; then
            echo "Moving $bundle to $BUILD_OUTPUT_DIR/"
            mv "$bundle" "$BUILD_OUTPUT_DIR/"
        fi
    done

    echo "✓ $plugin_name build complete"

    # Return to script directory for next iteration
    cd "$SCRIPT_DIR" || { echo "Error: Cannot cd to $SCRIPT_DIR at end of iteration"; exit 1; }
done

echo ""
echo "========================================"
echo "Build Complete!"
echo "========================================"
echo "All plugin bundles are in: $BUILD_OUTPUT_DIR"
ls -la "$BUILD_OUTPUT_DIR"
