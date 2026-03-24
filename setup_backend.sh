#!/usr/bin/env bash
# StemSplitter backend setup
# Creates ~/.stemsplitter/venv and installs Demucs + PyTorch

set -e

VENV_DIR="$HOME/.stemsplitter/venv"

echo "=== StemSplitter Backend Setup ==="
echo ""

# Check for Python 3.9+
if ! command -v python3 &>/dev/null; then
    echo "ERROR: python3 not found. Install it from https://www.python.org or via Homebrew:"
    echo "  brew install python"
    exit 1
fi

PY_VERSION=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
PY_MAJOR=$(python3 -c "import sys; print(sys.version_info.major)")
PY_MINOR=$(python3 -c "import sys; print(sys.version_info.minor)")

if [ "$PY_MAJOR" -lt 3 ] || { [ "$PY_MAJOR" -eq 3 ] && [ "$PY_MINOR" -lt 9 ]; }; then
    echo "ERROR: Python 3.9 or newer is required (found $PY_VERSION)."
    exit 1
fi

echo "✓ Python $PY_VERSION found"

# Check for ffmpeg
if ! command -v ffmpeg &>/dev/null; then
    echo ""
    echo "ffmpeg is not installed. Attempting to install via Homebrew..."
    if command -v brew &>/dev/null; then
        brew install ffmpeg
    else
        echo "ERROR: Homebrew not found. Please install ffmpeg manually:"
        echo "  1. Install Homebrew: https://brew.sh"
        echo "  2. Then run: brew install ffmpeg"
        exit 1
    fi
fi

echo "✓ ffmpeg found"

# Create venv
echo ""
echo "Creating virtual environment at $VENV_DIR ..."
mkdir -p "$HOME/.stemsplitter"
python3 -m venv "$VENV_DIR"
echo "✓ Virtual environment created"

# Upgrade pip
echo ""
echo "Upgrading pip..."
"$VENV_DIR/bin/pip" install --upgrade pip --quiet

# Install dependencies
echo ""
echo "Installing PyTorch (this may take a few minutes)..."
"$VENV_DIR/bin/pip" install torch torchaudio --quiet

echo "Installing Demucs..."
"$VENV_DIR/bin/pip" install demucs --quiet

echo "Installing rumps (menu bar framework)..."
"$VENV_DIR/bin/pip" install rumps --quiet

echo "Installing ffmpeg-python..."
"$VENV_DIR/bin/pip" install ffmpeg-python --quiet

# Validate
echo ""
echo "Validating installation..."
"$VENV_DIR/bin/python3" -c "import demucs; import torch; print(f'✓ Demucs OK  |  PyTorch {torch.__version__}')"

echo ""
echo "=== Setup complete! ==="
echo ""
echo "To run StemSplitter:"
echo "  source $VENV_DIR/bin/activate"
echo "  python stemsplitter.py"
echo ""
echo "Or just run:  python stemsplitter.py"
echo "(it will auto-detect the venv at $VENV_DIR)"
echo ""
echo "Note: The first separation will download the Demucs model (~80 MB)."
