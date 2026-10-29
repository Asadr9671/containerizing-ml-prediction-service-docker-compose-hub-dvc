"""Publish assignment image and prove anonymous clean-room consumption."""
import json
import shutil
import subprocess
import urllib.request
from evidence import ROOT, TOOLS, run, docker, py

image='asad3390/breast-cancer-triage-api'
docker(16,'tag',image+':1.0.0',image+':latest')
docker(16,'push',image+':1.0.0')
docker(16,'push',image+':latest')
tags={}
for tag in ('1.0.0','latest'):
    url=f'https://hub.docker.com/v2/repositories/{image}/tags/{tag}'
    data=json.load(urllib.request.urlopen(url))
    tags[tag]=data['digest']
    py(16,f"import urllib.request,json; d=json.load(urllib.request.urlopen('{url}')); print(json.dumps({{k:d.get(k) for k in ['name','digest','full_size','last_updated']}},indent=2))")
assert tags['1.0.0']==tags['latest']
docker(17,'compose','down')
docker(17,'rm','-f','a02-standalone','a02-config')
all_ids=subprocess.check_output(['docker','image','ls','-aq'],text=True).split()
owned=[]
for image_id in dict.fromkeys(all_ids):
    info=json.loads(subprocess.check_output(['docker','image','inspect',image_id],text=True))[0]
    if any(value.startswith(image+'@') for value in info.get('RepoDigests',[])):
        owned.append(info['Id'])
docker(17,'rmi',image+':naive',image+':latest',image+':1.0.0')
for image_id in owned:
    exists=subprocess.run(['docker','image','inspect',image_id],capture_output=True).returncode==0
    if exists:
        docker(17,'rmi',image_id)
docker(17,'image','ls',image)
clean=ROOT.parent/'clean-room'
clean.mkdir(exist_ok=True)
shutil.copy(ROOT/'docker-compose.hub.yml',clean/'docker-compose.hub.yml')
shutil.copy(ROOT/'.env',clean/'.env')
assert {p.name for p in clean.iterdir()}=={'.env','docker-compose.hub.yml'}
run(17,['python','-c',"from pathlib import Path; print('Clean-room files:',sorted(p.name for p in Path('.').iterdir()))"],cwd=clean)
anonymous=TOOLS/'anonymous-docker'
anonymous.mkdir(exist_ok=True)
(anonymous/'config.json').write_text('{}')
args=['docker','--config',str(anonymous),'--host','npipe:////./pipe/dockerDesktopLinuxEngine','compose','-f','docker-compose.hub.yml']
run(17,[*args,'pull'],cwd=clean)
run(17,[*args,'up','-d','--wait'],cwd=clean)
run(17,[*args,'ps'],cwd=clean)
# Generate payload in memory; the clean room still contains only its two config files.
payload=json.loads((ROOT/'sample.json').read_text())
code="import json,urllib.request; payload="+repr(payload)+"; r=urllib.request.urlopen(urllib.request.Request('http://localhost:8000/predict',data=json.dumps(payload).encode(),headers={'Content-Type':'application/json'})); print('POST /predict',r.status,r.read().decode()); assert r.status==200"
run(17,['python','-c',code],cwd=clean)
digest=json.loads(docker(17,'image','inspect','--format','{{json .RepoDigests}}',image+':1.0.0'))
assert any(tags['1.0.0'] in item for item in digest)
py(17,f"print('Docker Hub digest:', {tags['1.0.0']!r}); print('Pulled RepoDigests:', {digest!r}); print('MATCH: anonymous pull and clean-room prediction passed')")
(ROOT/'evidence/published.json').write_text(json.dumps({'image':image,'tags':tags,'anonymous_pull':True,'clean_room_prediction':True},indent=2))
