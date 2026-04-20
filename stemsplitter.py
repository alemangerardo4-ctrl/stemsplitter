#!/usr/bin/env python3
import os
import rumps
import subprocess
import threading
import tempfile
import sys
from pathlib import Path

VENV_PATH = Path.home() / ".stemsplitter" / "venv"
VENV_PYTHON = VENV_PATH / "bin" / "python3"


def find_venv_python():
    if sys.prefix != sys.base_prefix:
        return Path(sys.prefix) / "bin" / "python3"
    if VENV_PYTHON.exists():
        return VENV_PYTHON
    return None


def _find_bundle_resource(filename):
    """Find a resource file in the .app bundle Resources or alongside this script."""
    resource_path = os.environ.get('RESOURCEPATH')
    if resource_path:
        candidate = Path(resource_path) / filename
        if candidate.exists():
            return candidate
    candidate = Path(__file__).parent / filename
    if candidate.exists():
        return candidate
    return None


def _osascript(script):
    return subprocess.run(['osascript', '-e', script], capture_output=True, text=True)


def auto_setup_if_needed():
    """Run first-time backend setup if the venv is missing. Returns False to abort launch."""
    if find_venv_python():
        return True

    setup_script = _find_bundle_resource('setup_backend.sh')
    if not setup_script:
        _osascript(
            'display alert "StemSplitter \u2014 Setup Required" '
            'message "The backend setup script was not found inside the app bundle. '
            'Please re-download StemSplitter." '
            'as critical buttons {"Quit"} default button "Quit"'
        )
        return False

    r = _osascript(
        'button returned of (display dialog '
        '"StemSplitter needs to install its AI backend.\n\n'
        'This is a one-time setup that downloads about 2 GB '
        '(PyTorch + Demucs) and takes several minutes.\n'
        'The app will launch automatically when complete.\n\n'
        'Click Install to begin." '
        'buttons {"Cancel", "Install"} default button "Install" '
        'with title "StemSplitter \u2014 First-Time Setup")'
    )
    if r.returncode != 0 or r.stdout.strip() != 'Install':
        return False

    _osascript(
        'display notification "Installing StemSplitter backend. This will take several minutes..." '
        'with title "StemSplitter" subtitle "First-time setup in progress"'
    )

    proc = subprocess.run(['bash', str(setup_script)], capture_output=True, text=True)

    if proc.returncode == 0:
        _osascript(
            'display notification "StemSplitter is ready to use!" '
            'with title "StemSplitter" subtitle "Setup complete"'
        )
        return True

    _osascript(
        'display alert "StemSplitter Setup Failed" '
        'message "Installation failed.\n\n'
        'Please ensure Python 3.9+ and Homebrew are installed, then relaunch StemSplitter.\n\n'
        '    brew install python ffmpeg" '
        'as critical buttons {"OK"} default button "OK"'
    )
    return False


class StemApp(rumps.App):
    def __init__(self):
        super().__init__("🎧", quit_button=rumps.MenuItem('Quit'))
        self.output_dir = Path.home() / "Desktop" / "stems"
        self.output_dir.mkdir(exist_ok=True)
        self.venv_python = find_venv_python()
        if not self.venv_python:
            rumps.alert(
                "StemSplitter — Backend Not Found",
                "The Python backend is not installed.\n\n"
                "Please run the setup script first:\n\n"
                "  bash setup_backend.sh\n\n"
                "This will install Demucs, PyTorch, and other dependencies (~2 GB)."
            )
            rumps.quit_application()
        self.mode = "2"
        self.separating = False
        self.m2 = rumps.MenuItem('⚡ 2-Stem (vocals + instrumental)', callback=self.set2)
        self.m4 = rumps.MenuItem('🎛️  4-Stem (vocals, drums, bass, other)', callback=self.set4)
        self.m2.state = True
        self.status = rumps.MenuItem('Status: Ready')
        self.menu = [
            rumps.MenuItem('Separate Audio...', callback=self.pick),
            rumps.separator,
            self.m2,
            self.m4,
            rumps.separator,
            rumps.MenuItem('Output: ~/Desktop/stems/'),
            self.status,
        ]

    def set2(self, _):
        self.mode = "2"
        self.m2.state = True
        self.m4.state = False

    def set4(self, _):
        self.mode = "4"
        self.m2.state = False
        self.m4.state = True

    @rumps.clicked('Separate Audio...')
    def pick(self, _):
        if self.separating:
            rumps.alert("Busy", "Already separating a file. Please wait.")
            return
        try:
            r = subprocess.run(
                ['osascript', '-e', 'tell app "Finder"\nactivate\nPOSIX path of (choose file)\nend tell'],
                capture_output=True, text=True, timeout=120
            )
            if r.returncode == 0 and r.stdout.strip():
                f = Path(r.stdout.strip())
                if f.exists():
                    threading.Thread(target=self.sep, args=(f,), daemon=True).start()
        except Exception:
            pass

    def sep(self, f):
        self.separating = True
        self.title = "🎧⏳"
        self.status.title = 'Status: Separating...'
        rumps.notification("StemSplitter", f.name, f"{self.mode}-stem mode", sound=False)
        try:
            tw = Path(tempfile.gettempdir()) / f"{f.stem}.wav"
            subprocess.run(
                ['ffmpeg', '-y', '-i', str(f), '-ar', '44100', '-ac', '2', str(tw)],
                capture_output=True, timeout=60, check=True
            )
            code = (
                'import os\n'
                'os.environ["TORCHAUDIO_USE_BACKEND_DISPATCHER"] = "0"\n'
                'import sys\n'
                'from demucs.separate import main\n'
                f'sys.argv = ["demucs"]\n'
                f'if "{self.mode}" == "2":\n'
                f'    sys.argv += ["--two-stems", "vocals"]\n'
                f'sys.argv += ["--mp3", "-o", "{self.output_dir}", "{tw}"]\n'
                'main()\n'
            )
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as t:
                t.write(code)
                ts = t.name
            r = subprocess.run([str(self.venv_python), ts], capture_output=True, timeout=600)
            Path(ts).unlink()
            tw.unlink()
            if r.returncode == 0:
                out = self.output_dir / "htdemucs" / f.stem
                if out.exists():
                    rumps.notification("StemSplitter ✅", "Done!", f"{len(list(out.glob('*.mp3')))} stems saved", sound=True)
                    subprocess.run(["open", str(out)])
                else:
                    raise Exception("Output folder not found — separation may have failed")
            else:
                stderr = r.stderr.decode(errors='replace')[-200:] if r.stderr else "unknown error"
                raise Exception(stderr)
        except subprocess.CalledProcessError:
            rumps.notification("StemSplitter ❌", "Error", "ffmpeg failed — is ffmpeg installed? (brew install ffmpeg)", sound=True)
        except Exception as e:
            rumps.notification("StemSplitter ❌", "Error", str(e)[:150], sound=True)
        finally:
            self.separating = False
            self.title = "🎧"
            self.status.title = 'Status: Ready'


if __name__ == '__main__':
    if not auto_setup_if_needed():
        sys.exit(0)
    StemApp().run()
