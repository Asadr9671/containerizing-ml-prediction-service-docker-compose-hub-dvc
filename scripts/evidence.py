"""Execute real commands and retain their unedited combined output as JSON/text."""
import datetime
import json
import os
from pathlib import Path
import subprocess
import time

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT.parent / '.tools'
os.environ['PATH'] = str(TOOLS/'python') + os.pathsep + str(TOOLS/'python/Scripts') + os.pathsep + str(TOOLS/'git/cmd') + os.pathsep + os.environ['PATH']
os.environ['PYTHONUTF8'] = '1'
os.environ['DVC_NO_ANALYTICS'] = 'true'
os.chdir(ROOT)

def run(task, args, expected=0, cwd=None):
    command = subprocess.list2cmdline([str(x) for x in args])
    print('$ ' + command, flush=True)
    start = time.perf_counter()
    result = subprocess.run(args, cwd=cwd or ROOT, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                            encoding='utf-8', errors='replace')
    seconds = time.perf_counter()-start
    print(result.stdout, flush=True)
    record = {'task': task, 'command': command, 'output': result.stdout, 'exit_code': result.returncode,
              'seconds': round(seconds, 3), 'timestamp': datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=5))).isoformat()}
    folder = ROOT/'evidence'
    folder.mkdir(exist_ok=True)
    with (folder/'commands.jsonl').open('a', encoding='utf-8') as f:
        f.write(json.dumps(record)+'\n')
    if expected is not None and result.returncode != expected:
        raise RuntimeError(f'Unexpected exit {result.returncode}: {command}')
    return result.stdout

def py(task, code):
    return run(task, ['python', '-c', code])

def docker(task, *args, expected=0):
    return run(task, ['docker', *args], expected=expected)
