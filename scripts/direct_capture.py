"""Run commands in a real Windows console and capture the console window pixels.

No image generation or HTML rendering is used. Command output is paginated in the
console for readability; original output and exit status are retained in JSONL.
"""
import ctypes
import datetime
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import textwrap

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT.parent/'.tools'
CONTROL = TOOLS/'direct-capture'
CONTROL.mkdir(exist_ok=True)
TITLE = 'MLOps Assignment 02 - Live command verification'

def read_control(path):
    try:
        return json.loads(path.read_text())
    except (json.JSONDecodeError, FileNotFoundError, PermissionError):
        return {}

def environment():
    env=os.environ.copy()
    env['PATH']=str(TOOLS/'python')+os.pathsep+str(TOOLS/'python/Scripts')+os.pathsep+str(TOOLS/'git/cmd')+os.pathsep+env['PATH']
    env['PYTHONUTF8']='1'
    env['DVC_NO_ANALYTICS']='true'
    env['DVC_SITE_CACHE_DIR']=str(TOOLS/'dvc-site-cache')
    return env

def worker():
    sys.stdout.reconfigure(encoding='utf-8',errors='replace')
    ctypes.windll.kernel32.SetConsoleTitleW(TITLE)
    os.system('mode con: cols=132 lines=42')
    last=None
    while True:
        jobpath=CONTROL/'job.json'
        if not jobpath.exists():
            time.sleep(.1);continue
        job=read_control(jobpath)
        if not job:
            time.sleep(.1);continue
        if job['id']==last:
            time.sleep(.1);continue
        last=job['id']
        if job.get('stop'):
            return
        os.chdir(job.get('cwd',str(ROOT)))
        cmd=job['command']
        os.system('cls')
        print('Task',job['task'],'|',job['title'],flush=True)
        print('PS>',cmd,flush=True)
        started=time.perf_counter()
        result=subprocess.run(['powershell.exe','-NoProfile','-Command',cmd],env=environment(),
            stdout=subprocess.PIPE,stderr=subprocess.STDOUT,encoding='utf-8',errors='replace')
        stamp=datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=5))).isoformat()
        record={**job,'output':result.stdout,'exit_code':result.returncode,'timestamp':stamp,'seconds':round(time.perf_counter()-started,3)}
        with (ROOT/'evidence/direct_commands.jsonl').open('a',encoding='utf-8') as f:
            f.write(json.dumps(record)+'\n')
        lines=[]
        raw=result.stdout.splitlines()
        if job.get('build') and len(raw)>65:
            selected=[line for line in raw if 'CACHED' in line or 'RUN ' in line or 'COPY ' in line or 'Quality gate' in line or 'DONE ' in line]
            raw=raw[:4]+['[Build output excerpt; unabridged output saved in evidence/direct_commands.jsonl]']+selected+raw[-10:]
        for line in raw:
            lines.extend(textwrap.wrap(line,width=126,replace_whitespace=False,drop_whitespace=False) or [''])
        chunks=[lines[n:n+20] for n in range(0,len(lines),20)] or [['(No output)']]
        for page,chunk in enumerate(chunks,1):
            os.system('cls')
            print(f"Task {job['task']} | {job['title']} | Output page {page}/{len(chunks)}")
            print(stamp,'| Exit:',result.returncode)
            print('-'*125)
            print('\n'.join(textwrap.wrap('PS> '+cmd,126)))
            print('-'*125)
            print('\n'.join(chunk))
            print('\n[Actual command output. Direct screenshot of this console window.]',flush=True)
            marker={'id':last,'page':page,'pages':len(chunks),'exit_code':result.returncode}
            (CONTROL/'ready.json').write_text(json.dumps(marker))
            while read_control(CONTROL/'ack.json')!=marker:
                time.sleep(.1)
        (CONTROL/'done.json').write_text(json.dumps({'id':last,'exit_code':result.returncode}))

def find_window():
    user32=ctypes.windll.user32
    found=[]
    callback=ctypes.WINFUNCTYPE(ctypes.c_bool,ctypes.c_void_p,ctypes.c_void_p)
    @callback
    def visit(hwnd,lparam):
        buffer=ctypes.create_unicode_buffer(512)
        user32.GetWindowTextW(hwnd,buffer,512)
        if TITLE in buffer.value and user32.IsWindowVisible(hwnd):
            found.append(hwnd)
        return True
    user32.EnumWindows(visit,0)
    return found[0] if found else None

def execute(jobs):
    from PIL import ImageGrab
    import ctypes.wintypes
    manifest_path=ROOT/'evidence/direct_screenshots.json'
    manifest=json.loads(manifest_path.read_text()) if manifest_path.exists() else []
    output=ROOT/'evidence/direct-screenshots'
    output.mkdir(exist_ok=True)
    worker_process=subprocess.Popen([sys.executable,str(Path(__file__).resolve()),'--worker'],
        cwd=ROOT,env=environment(),creationflags=subprocess.CREATE_NEW_CONSOLE)
    try:
        configured=set()
        for job in jobs:
            job={**job,'id':str(time.time_ns())}
            (CONTROL/'job.json').write_text(json.dumps(job))
            seen=set()
            deadline=time.time()+1200
            while time.time()<deadline:
                ready=CONTROL/'ready.json'
                if ready.exists():
                    marker=read_control(ready)
                    if marker.get('id')==job['id'] and marker['page'] not in seen:
                        hwnd=find_window()
                        if not hwnd:
                            raise RuntimeError('Visible console window not found')
                        user32=ctypes.windll.user32
                        user32.ShowWindow(hwnd,9)
                        user32.MoveWindow(hwnd,0,0,min(1280,user32.GetSystemMetrics(0)),min(780,user32.GetSystemMetrics(1)),True)
                        user32.SetForegroundWindow(hwnd)
                        if hwnd not in configured:
                            for _ in range(2):
                                user32.keybd_event(0x11,0,0,0)
                                user32.keybd_event(0xBD,0,0,0)
                                user32.keybd_event(0xBD,0,2,0)
                                user32.keybd_event(0x11,0,2,0)
                                time.sleep(.1)
                            configured.add(hwnd)
                        time.sleep(.4)
                        rect=ctypes.wintypes.RECT()
                        user32.GetWindowRect(hwnd,ctypes.byref(rect))
                        target=output/f"task{job['task']:02d}-{job['id']}-{marker['page']:02d}.png"
                        ImageGrab.grab(bbox=(max(0,rect.left),max(0,rect.top),min(user32.GetSystemMetrics(0),rect.right),min(user32.GetSystemMetrics(1),rect.bottom)),all_screens=True).save(target)
                        manifest.append({'task':job['task'],'title':job['title'],'command':job['command'],
                            'path':str(target.relative_to(ROOT)),'exit_code':marker['exit_code']})
                        manifest_path.write_text(json.dumps(manifest,indent=2))
                        seen.add(marker['page'])
                        (CONTROL/'ack.json').write_text(json.dumps(marker))
                done=CONTROL/'done.json'
                if done.exists():
                    value=read_control(done)
                    if value.get('id')==job['id']:
                        print(f"Captured task {job['task']}: {job['title']} (exit {value['exit_code']})",flush=True)
                        if value['exit_code']!=job.get('expected',0):
                            raise RuntimeError(f"Unexpected command exit: {job['command']}")
                        break
                time.sleep(.1)
            else:
                raise TimeoutError(job['command'])
    finally:
        (CONTROL/'job.json').write_text(json.dumps({'id':str(time.time_ns()),'stop':True}))
        try:worker_process.wait(timeout=5)
        except subprocess.TimeoutExpired:worker_process.terminate()

if __name__=='__main__':
    if '--worker' in sys.argv:
        worker()
    else:
        execute(json.loads(Path(sys.argv[1]).read_text(encoding='utf-8-sig')))
