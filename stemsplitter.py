#!/usr/bin/env python3
import rumps,subprocess,threading,tempfile,os
from pathlib import Path

class StemApp(rumps.App):
    def __init__(self):
        super().__init__("🎧", quit_button=rumps.MenuItem('Quit'))
        self.output_dir = Path.home()/"Desktop"/"stems"
        self.output_dir.mkdir(exist_ok=True)
        self.venv_python=None
        for b in [Path.home()/"music-tools",Path.home()/"music-tools-FINAL-TEST"]:
            v=b/"venv"/"bin"/"python3"
            if v.exists(): self.venv_python=v;break
        if not self.venv_python: rumps.alert("Error","Backend missing");rumps.quit_application()
        self.mode="2"
        self.separating=False
        self.m2=rumps.MenuItem('⚡ 2-Stem',callback=self.set2)
        self.m4=rumps.MenuItem('🎛️  4-Stem',callback=self.set4)
        self.m2.state=True
        self.status=rumps.MenuItem('Status: Ready')
        self.menu=[rumps.MenuItem('Separate Audio...',callback=self.pick),rumps.separator,self.m2,self.m4,rumps.separator,rumps.MenuItem('Output: ~/Desktop/stems/'),self.status]
    def set2(self,_): self.mode="2";self.m2.state=True;self.m4.state=False
    def set4(self,_): self.mode="4";self.m2.state=False;self.m4.state=True
    @rumps.clicked('Separate Audio...')
    def pick(self,_):
        if self.separating: rumps.alert("Busy","Separating...");return
        try:
            r=subprocess.run(['osascript','-e','tell app "Finder"\nactivate\nPOSIX path of (choose file)\nend tell'],capture_output=True,text=True,timeout=120)
            if r.returncode==0 and r.stdout.strip():
                f=Path(r.stdout.strip())
                if f.exists(): threading.Thread(target=self.sep,args=(f,),daemon=True).start()
        except: pass
    def sep(self,f):
        self.separating=True;self.title="🎧⏳";self.status.title='Status: Separating...'
        rumps.notification("StemSplitter",f.name,f"{self.mode}-stem mode",sound=False)
        try:
            tw=Path(tempfile.gettempdir())/f"{f.stem}.wav"
            subprocess.run(['ffmpeg','-y','-i',str(f),'-ar','44100','-ac','2',str(tw)],capture_output=True,timeout=60,check=True)
            code=f'import os\nos.environ["TORCHAUDIO_USE_BACKEND_DISPATCHER"]="0"\nimport sys\nfrom demucs.separate import main\nsys.argv=["demucs"]\nif "{self.mode}"=="2": sys.argv+=["--two-stems","vocals"]\nsys.argv+=["--mp3","-o","{self.output_dir}","{tw}"]\nmain()'
            with tempfile.NamedTemporaryFile(mode='w',suffix='.py',delete=False) as t: t.write(code);ts=t.name
            r=subprocess.run([str(self.venv_python),ts],capture_output=True,timeout=600)
            Path(ts).unlink();tw.unlink()
            if r.returncode==0:
                out=self.output_dir/"htdemucs"/f.stem
                if out.exists():
                    rumps.notification("StemSplitter ✅","Done!",f"{len(list(out.glob('*.mp3')))} stems",sound=True)
                    subprocess.run(["open",str(out)])
                else: raise Exception("Output missing")
            else: raise Exception("Failed")
        except Exception as e: rumps.notification("StemSplitter ❌","Error",str(e)[:100],sound=True)
        finally: self.separating=False;self.title="🎧";self.status.title='Status: Ready'

if __name__=='__main__': StemApp().run()
