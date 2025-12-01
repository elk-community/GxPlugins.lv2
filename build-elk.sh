#!/bin/bash

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Create build-elk folder
echo -e "${BLUE}Creating build-elk folder...${NC}"
mkdir -p build-elk

# Iterate over all Gx* folders
for plugin_dir in Gx*.lv2; do
    if [ ! -d "$plugin_dir" ]; then
        continue
    fi

    echo -e "${GREEN}Processing $plugin_dir...${NC}"

    cd "$plugin_dir"

    # Check if Makefile exists
    if [ ! -f "Makefile" ]; then
        echo -e "${RED}Warning: No Makefile found in $plugin_dir, skipping...${NC}"
        cd ..
        continue
    fi

    # Apply patch to remove CPU optimization section
    echo "  Patching Makefile..."

    # Find the line numbers to delete
    start=$(grep -n "check CPU and supported optimization flags" Makefile | head -1 | cut -d: -f1)
    end=$(grep -n "set bundle name" Makefile | head -1 | cut -d: -f1)

    if [ -n "$start" ] && [ -n "$end" ]; then
        # Delete from start to end-2 (to skip the blank line before "set bundle name")
        end=$((end - 2))
        sed -i.bak "${start},${end}d" Makefile
        echo "  Removed CPU optimization block (lines $start-$end)"
    else
        echo "  CPU optimization block not found in Makefile"
    fi

    # Build the plugin
    echo "  Building plugin..."
    make CROSS=$CROSS_COMPILE mod

    # Find and move the .lv2 folder to build-elk
    lv2_folder=$(find . -maxdepth 1 -name "*.lv2" -type d | head -n 1)
    if [ -n "$lv2_folder" ]; then
        echo "  Moving $lv2_folder to build-elk..."
        mv "$lv2_folder" ../build-elk/
    else
        echo -e "${RED}Warning: No .lv2 folder found after build in $plugin_dir${NC}"
    fi

    # Restore original Makefile (optional - comment out if you want to keep the patched version)
    mv Makefile.bak Makefile

    cd ..
    echo ""
done

echo -e "${GREEN}Build complete! All plugins are in the build-elk folder.${NC}"
