#!/bin/sh
# SPDX-License-Identifier: MIT
# Installation script for zoseza

# Default to /usr/local, but allow the user to override via the PREFIX environment variable
PREFIX=${PREFIX:-/usr/local}
BIN_DIR="$PREFIX/bin"
MAN_DIR="$PREFIX/man/man1"

echo "Preparing to install zoseza..."

# Create target directories if they don't exist
if [ ! -d "$BIN_DIR" ]; then
    echo "Creating directory: $BIN_DIR"
    mkdir -p "$BIN_DIR"
fi

if [ ! -d "$MAN_DIR" ]; then
    echo "Creating directory: $MAN_DIR"
    mkdir -p "$MAN_DIR"
fi

# Copy the Python script and drop the .py extension for a cleaner command name
echo "Installing executable to $BIN_DIR/zoseza..."
cp zoseza.py "$BIN_DIR/zoseza"
chmod 755 "$BIN_DIR/zoseza"

# Copy the manpage
echo "Installing manpage to $MAN_DIR/zoseza.1..."
cp zoseza.1 "$MAN_DIR/zoseza.1"
chmod 644 "$MAN_DIR/zoseza.1"

echo ""
echo "Installation complete!"
echo "--------------------------------------------------------"
echo "Make sure your environment variables are configured:"
echo "  export PATH=\"$BIN_DIR:\$PATH\""
echo "  export MANPATH=\"$PREFIX/man:\$MANPATH\""
echo "--------------------------------------------------------"
