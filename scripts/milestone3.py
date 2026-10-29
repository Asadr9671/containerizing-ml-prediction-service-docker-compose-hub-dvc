import json
import time
from evidence import ROOT, run, docker, py

sha = run(10, ['git', 'rev-parse', 'HEAD']).strip()
image = 'asad3390/breast-cancer-triage-api'
timings = json.loads((ROOT/'evidence/build_comparison.json').read_text()) if (ROOT/'evidence/build_comparison.json').exists() else []
for task, filename, tag in [(10, 'Dockerfile.naive', 'naive'), (11, 'Dockerfile', '1.0.0')]:
    if any(row['image']==tag for row in timings):
        continue
    args = ['build', '--progress=plain', '--build-arg', 'MODEL_VERSION=1.0.0', '--build-arg', f'GIT_SHA={sha}', '-f', filename, '-t', f'{image}:{tag}', '.']
    start = time.perf_counter()
    docker(task, *args[:1], '--no-cache', *args[1:])
    cold = time.perf_counter()-start
    py(task, "from pathlib import Path; p=Path('app/main.py'); p.write_text(p.read_text()+'\\n# Application-only rebuild demonstration.\\n'); print('Added one comment line to app/main.py')")
    start = time.perf_counter()
    docker(task, *args)
    rebuild = time.perf_counter()-start
    info = json.loads(docker(task, 'image', 'inspect', f'{image}:{tag}'))[0]
    timings.append({'image': tag, 'base': 'ubuntu:22.04' if tag=='naive' else 'python:3.12.10-slim-bookworm', 'size_bytes': info['Size'], 'cold_seconds': round(cold,2), 'rebuild_seconds': round(rebuild,2), 'user': info['Config'].get('User') or 'root'})
    (ROOT/'evidence/build_comparison.json').write_text(json.dumps(timings, indent=2))
docker(12, 'run', '-d', '--name', 'a02-standalone', '-p', '18000:8000', f'{image}:1.0.0')
time.sleep(18)
run(12, ['python', 'scripts/probe_api.py', '--url', 'http://localhost:18000'])
docker(12, 'inspect', '--format', '{{.State.Health.Status}}', 'a02-standalone')
docker(12, 'logs', 'a02-standalone')
docker(12, 'history', f'{image}:1.0.0')
docker(12, 'image', 'inspect', '--format', '{{json .Config}}', f'{image}:1.0.0')
docker(12, 'exec', 'a02-standalone', 'python', '-c', "import os,importlib.util; print('uid=',os.getuid()); print('dataset present=',os.path.exists('/app/data')); print('pandas=',importlib.util.find_spec('pandas')); print('yaml=',importlib.util.find_spec('yaml')); assert os.getuid()!=0; assert not os.path.exists('/app/data'); assert importlib.util.find_spec('pandas') is None")
docker(12, 'run', '-d', '--name', 'a02-config', '-p', '18001:8000', '-e', 'DECISION_THRESHOLD=0.99', '-e', 'LOG_LEVEL=DEBUG', f'{image}:1.0.0')
time.sleep(8)
run(12, ['python', 'scripts/probe_api.py', '--url', 'http://localhost:18001', '--threshold', '0.99'])
docker(12, 'logs', 'a02-config')
run(12, ['git', 'add', 'Dockerfile', 'Dockerfile.naive', '.dockerignore', 'app/main.py', 'scripts/milestone3.py', 'scripts/probe_api.py'])
run(12, ['git', 'commit', '-m', 'Milestone 3: build and benchmark non-root multi-stage serving image'])
