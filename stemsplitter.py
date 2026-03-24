#!/usr/bin/env python3
import rumps, subprocess, threading, tempfile, os, sys
from pathlib import Path

VENV_PATH = Path.home() / ".stemsplitter" / "venv"

def find_venv_python():
    # If already running inside a venv, use it directly
    if sys.prefix != sys.base_prefix:
        return Path(sys.prefix) / "bin" / "python3"
    # Check standard install location
    candidate = VENV_PATH / "bin" / "python3"
    if candidate.exists():
        return candidate
    return None

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
    StemApp().run()
