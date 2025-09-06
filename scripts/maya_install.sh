#!/bin/bash
# Install Vogue Manager Maya integration
# Unix/Linux shell script

echo "Installing Vogue Manager Maya integration..."

# Get Maya scripts directory
MAYA_SCRIPTS_DIR="$HOME/Documents/maya/scripts"
if [ ! -d "$MAYA_SCRIPTS_DIR" ]; then
    echo "Creating Maya scripts directory: $MAYA_SCRIPTS_DIR"
    mkdir -p "$MAYA_SCRIPTS_DIR"
fi

# Copy vogue_maya module
echo "Copying vogue_maya module..."
cp -r "$(dirname "$0")/../src/vogue_maya" "$MAYA_SCRIPTS_DIR/"

# Copy vogue_core module
echo "Copying vogue_core module..."
cp -r "$(dirname "$0")/../src/vogue_core" "$MAYA_SCRIPTS_DIR/"

# Copy shelf script
echo "Installing shelf script..."
cp "$(dirname "$0")/../src/vogue_maya/shelf.mel" "$MAYA_SCRIPTS_DIR/vogue_manager_shelf.mel"

echo ""
echo "Installation complete!"
echo ""
echo "To use Vogue Manager in Maya:"
echo "1. Start Maya"
echo "2. Run: python(\"import vogue_maya.tool as vm; vm.show_vogue_manager()\")"
echo "3. Or use the shelf button if installed"
echo ""
