"""Repeat clean-room verification, removing only assignment-owned images."""
import json
import subprocess
from evidence import ROOT, TOOLS, run, docker

image='asad3390/breast-cancer-triage-api'
docker(17,'compose','-p','a02-direct','down','-v')
docker(17,'compose','-f','../clean-room/docker-compose.hub.yml','down')
for name in ('a02-proof-standalone','a02-proof-config'):
    if subprocess.run(['docker','container','inspect',name],capture_output=True).returncode==0:
        docker(17,'rm','-f',name)
ids=subprocess.check_output(['docker','image','ls','-aq'],text=True).split()
for identifier in dict.fromkeys(ids):
    info=json.loads(subprocess.check_output(['docker','image','inspect',identifier],text=True))[0]
    tags=info.get('RepoTags',[])
    owned=any(tag.startswith(image+':') or tag.startswith('a02-proof-production:') for tag in tags)
    owned=owned or any(digest.startswith(image+'@') for digest in info.get('RepoDigests',[]))
    if owned:
        docker(17,'rmi','-f',info['Id'])
docker(17,'image','ls',image)
folder=ROOT.parent/'clean-room'
run(17,['python','-c',"from pathlib import Path; names=sorted(p.name for p in Path('.').iterdir()); print('Clean-room files:',names); assert names==['.env','docker-compose.hub.yml']"],cwd=folder)
anonymous=TOOLS/'anonymous-docker'
assert json.loads((anonymous/'config.json').read_text())=={}
args=['docker','--config',str(anonymous),'--host','npipe:////./pipe/dockerDesktopLinuxEngine','compose','-f','docker-compose.hub.yml']
run(17,[*args,'pull'],cwd=folder)
run(17,[*args,'up','-d','--wait'],cwd=folder)
run(17,[*args,'ps'],cwd=folder)
run(17,['python',str(ROOT/'scripts/probe_api.py')],cwd=ROOT)
docker(17,'image','inspect','--format','{{json .RepoDigests}}',image+':1.0.0')
digest=json.loads(subprocess.check_output(['docker','image','inspect','--format','{{json .RepoDigests}}',image+':1.0.0'],text=True))
expected=json.loads((ROOT/'evidence/published.json').read_text())['tags']['1.0.0']
assert any(expected in value for value in digest)
print('PASS: anonymous pull, healthy clean-room stack, successful prediction and matching digest')
