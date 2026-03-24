# StemSplitter

macOS menu bar app for AI-powered audio stem separation. Uses [Demucs](https://github.com/facebookresearch/demucs) to split any audio file into vocals, drums, bass, and other instruments.

Appears as a 🎧 icon in your menu bar. Outputs MP3 stems to `~/Desktop/stems/`.

## Requirements

- macOS 11 (Big Sur) or later
- Python 3.9+
- ffmpeg (installed automatically by setup script if you have Homebrew)
- ~2 GB disk space for PyTorch and the Demucs model

## Installation

```bash
git clone https://github.com/your-username/stemsplitter.git
cd stemsplitter
bash setup_backend.sh
```

The setup script creates a virtual environment at `~/.stemsplitter/venv` and installs all Python dependencies. The first time you separate a file, Demucs will also download its model (~80 MB).

## Running

```bash
python stemsplitter.py
```

The 🎧 icon appears in your menu bar. Click it to:
- **Separate Audio...** — pick any audio file (MP3, WAV, FLAC, etc.)
- **2-Stem** — splits into vocals + instrumental
- **4-Stem** — splits into vocals, drums, bass, other

Processing takes 1–5 minutes depending on file length. When done, the output folder opens automatically.

## Building a .app bundle (optional)

If you want a standalone `.app` that lives in Applications:

```bash
pip install py2app
python setup.py py2app
# Output: dist/StemSplitter.app
```

The bundled app still requires `~/.stemsplitter/venv` to be set up — run `setup_backend.sh` first.

## License

MIT

---

**Part of [PUBLIC WORKS](https://publicworks.design) — Open source audio tools for creators.**
