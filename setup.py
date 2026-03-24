# py2app build script — builds StemSplitter.app for macOS distribution
#
# Usage:
#   pip install py2app
#   python setup.py py2app
#
# Output: dist/StemSplitter.app
#
# Note: The app itself is a lightweight menu bar launcher. The heavy AI
# backend (Demucs, PyTorch) lives in ~/.stemsplitter/venv and is NOT
# bundled into the .app — users must run setup_backend.sh first.

from setuptools import setup

APP = ['stemsplitter.py']
OPTIONS = {
    'argv_emulation': False,
    'packages': ['rumps'],
    'plist': {
        'CFBundleName': 'StemSplitter',
        'CFBundleDisplayName': 'StemSplitter',
        'CFBundleIdentifier': 'design.publicworks.stemsplitter',
        'CFBundleVersion': '1.0.0',
        'LSUIElement': True,          # hide from Dock, show in menu bar only
        'NSHighResolutionCapable': True,
    },
}

setup(
    app=APP,
    options={'py2app': OPTIONS},
    setup_requires=['py2app'],
)
