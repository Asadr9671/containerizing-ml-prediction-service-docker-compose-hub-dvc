"""Repeat verification in a real Windows terminal for original screenshots."""
import argparse
import json
from pathlib import Path
from direct_capture import execute, ROOT

parser=argparse.ArgumentParser()
parser.add_argument('phase',choices=['github','basics','data','images','compose','registry'])
parser.add_argument('--skip',type=int,default=0)
options=parser.parse_args()
phase=options.phase
jobs=[]
def add(task,title,command,**kwargs):
    jobs.append(dict(task=task,title=title,command=command,**kwargs))

if phase=='github':
    add(19,'Create and publish public GitHub source repository',"& 'C:\\Program Files\\GitHub CLI\\gh.exe' repo create Asadr9671/containerizing-ml-prediction-service-docker-compose-hub-dvc --public --source . --remote origin --push")
    add(19,'Public repository and incremental milestone history',"& 'C:\\Program Files\\GitHub CLI\\gh.exe' repo view --json name,url,visibility; git log --oneline -8")
elif phase=='basics':
    add(1,'Docker client and engine', 'docker version')
    add(1,'Run hello-world twice','docker run --rm hello-world:linux; docker run --rm hello-world:linux')
    add(2,'nginx background service and host response','docker run -d --name a02-proof-nginx1 -p 18080:80 nginx:1.28.0-alpine; Start-Sleep 2; (Invoke-WebRequest -UseBasicParsing http://localhost:18080).StatusCode')
    add(2,'Expected occupied-port failure','docker run -d --name a02-proof-conflict -p 18080:80 nginx:1.28.0-alpine',expected=1)
    add(2,'Use a different port and inspect access logs','docker rm a02-proof-conflict; docker run -d --name a02-proof-nginx2 -p 18081:80 nginx:1.28.0-alpine; 1..3 | ForEach-Object { (Invoke-WebRequest -UseBasicParsing http://localhost:18080).StatusCode }; docker logs --tail 8 a02-proof-nginx1; docker ps --filter name=a02-proof-nginx')
    add(2,'Stop, list stopped, restart and safely remove','docker stop a02-proof-nginx1; docker ps -a --filter name=a02-proof-nginx; docker start a02-proof-nginx1; docker stop a02-proof-nginx1 a02-proof-nginx2; docker rm a02-proof-nginx1 a02-proof-nginx2')
    add(3,'Pull two Redis versions and compare sizes','docker pull redis:7.4.2; docker pull redis:7.4.2-alpine; docker image ls redis')
    add(3,'Ubuntu exits without an interactive command','docker run --name a02-proof-ubuntu ubuntu:22.04; docker ps -a --filter name=a02-proof-ubuntu')
    add(3,'Expected image-in-use removal error','docker rmi ubuntu:22.04',expected=1)
    add(3,'Safe removal order','docker rm a02-proof-ubuntu; docker rmi ubuntu:22.04')
    add(4,'Expected unconfigured PostgreSQL failure','docker run --name a02-proof-pg-fail postgres:16.8-alpine',expected=1)
    add(4,'Configure PostgreSQL and connect with psql','docker logs a02-proof-pg-fail; docker run -d --name a02-proof-pg -e POSTGRES_PASSWORD=assignment-local-demo -e POSTGRES_USER=student -e POSTGRES_DB=lab postgres:16.8-alpine; Start-Sleep 8; docker exec a02-proof-pg psql -U student -d lab -c "SELECT current_user, current_database();"')
    add(4,'Host bind mount changes without container restart',"Set-Content evidence/webroot/index.html '<h1>Original bind-mounted page</h1>'; (Invoke-WebRequest -UseBasicParsing http://localhost:18082).Content; Set-Content evidence/webroot/index.html '<h1>Updated live without restart</h1>'; (Invoke-WebRequest -UseBasicParsing http://localhost:18082).Content; docker inspect --format '{{.State.StartedAt}}' a02-bind")
    add(4,'Clean up temporary database exercise containers','docker stop a02-proof-pg; docker rm a02-proof-pg a02-proof-pg-fail')
elif phase=='data':
    add(5,'DVC tracking, remote and Git exclusion','dvc root; dvc remote list; Get-Content data/raw/breast_cancer.csv.dvc; git ls-files data/raw; git check-ignore data/raw/breast_cancer.csv; dvc push data/raw/breast_cancer.csv.dvc')
    add(5,'Restore working dataset with dvc pull',"Remove-Item -LiteralPath data/raw/breast_cancer.csv; dvc pull data/raw/breast_cancer.csv.dvc; python -c \"import pandas as pd; d=pd.read_csv('data/raw/breast_cancer.csv'); print('Rows:',len(d),'Features:',len(d.columns)-1,'Nulls:',d.isna().sum().sum())\"")
    add(6,'Restore original 569-row dataset','git checkout data-v1 -- data/raw/breast_cancer.csv.dvc; dvc checkout data/raw/breast_cancer.csv.dvc; python -c "import pandas as pd; print(len(pd.read_csv(\'data/raw/breast_cancer.csv\')))"')
    add(6,'Restore corrected 539-row dataset','git checkout data-v2 -- data/raw/breast_cancer.csv.dvc; dvc checkout data/raw/breast_cancer.csv.dvc; python -c "import pandas as pd; print(len(pd.read_csv(\'data/raw/breast_cancer.csv\')))"')
    add(7,'Train both model families and enforce recall gate','python -m training.train')
    add(8,'Execute pipeline then demonstrate unchanged skip','dvc repro --force; dvc repro')
    add(8,'Hyperparameter change invalidates the pipeline',"(Get-Content params.yaml -Raw).Replace('n_estimators: 160','n_estimators: 161') | Set-Content -Encoding ascii params.yaml; dvc repro")
    add(8,'Restore submitted hyperparameters and model','git restore params.yaml; dvc repro; dvc push')
    add(9,'API contract, validation and outage tests','python -m pytest -q -p no:cacheprovider tests; python scripts/probe_api.py --url http://localhost:8000')
elif phase=='images':
    add(10,'Rebuild working Ubuntu baseline','docker build --progress=plain -f Dockerfile.naive -t asad3390/breast-cancer-triage-api:naive-proof .',build=True)
    add(10,'Baseline image measurement and archived cold benchmark',"docker image inspect --format 'Size={{.Size}} User={{.Config.User}}' asad3390/breast-cancer-triage-api:naive-proof; Get-Content evidence/build_comparison.json")
    add(11,'Build production image from restored DVC data','dvc pull; docker build --progress=plain --build-arg MODEL_VERSION=1.0.0 --build-arg GIT_SHA=eaf11d64f2d498066217f734279554f4fc0115ec -t a02-proof-production:1.0.0 .',build=True)
    add(11,'Application edit reuses dependency layers',"Add-Content app/main.py '# Direct screenshot cache verification'; docker build --progress=plain --build-arg MODEL_VERSION=1.0.0 --build-arg GIT_SHA=eaf11d64f2d498066217f734279554f4fc0115ec -t a02-proof-production:1.0.0 .; git restore app/main.py",build=True)
    add(12,'Standalone container, prediction and runtime metadata','docker run -d --name a02-proof-standalone -p 18000:8000 a02-proof-production:1.0.0; Start-Sleep 12; python scripts/probe_api.py --url http://localhost:18000')
    add(12,'Healthy, non-root, correct port and healthcheck',"docker inspect --format '{{.State.Health.Status}}' a02-proof-standalone; docker image inspect --format 'User={{.Config.User}} Ports={{json .Config.ExposedPorts}} Health={{json .Config.Healthcheck}}' a02-proof-production:1.0.0; docker exec a02-proof-standalone id; docker logs --tail 8 a02-proof-standalone; docker history a02-proof-production:1.0.0")
    add(12,'Same image with a different threshold','docker run -d --name a02-proof-config -p 18001:8000 -e DECISION_THRESHOLD=0.99 -e LOG_LEVEL=DEBUG a02-proof-production:1.0.0; Start-Sleep 8; python scripts/probe_api.py --url http://localhost:18001 --threshold 0.99; docker logs --tail 5 a02-proof-config')
elif phase=='compose':
    # Isolated Compose project; the published clean-room stack remains available.
    add(14,'Compose configuration and healthy startup',"$env:API_PORT='18004'; docker compose -p a02-direct config; docker compose -p a02-direct up -d --build --wait; docker compose -p a02-direct ps",build=True)
    add(13,'Counter increases for three predictions',"$before=(Invoke-RestMethod http://localhost:18004/stats).predictions; Write-Output \"Before: $before\"; 1..3 | ForEach-Object { Invoke-RestMethod -Uri http://localhost:18004/predict -Method Post -ContentType application/json -InFile sample.json | ConvertTo-Json -Compress }; $after=(Invoke-RestMethod http://localhost:18004/stats).predictions; Write-Output \"After: $after\"; if($after -ne $before+3){exit 1}; $after | Set-Content evidence/direct-count.txt")
    add(13,'Redis outage does not stop inference',"$env:API_PORT='18004'; docker compose -p a02-direct stop redis; Invoke-RestMethod http://localhost:18004/health | ConvertTo-Json -Compress; Invoke-RestMethod -Uri http://localhost:18004/predict -Method Post -ContentType application/json -InFile sample.json | ConvertTo-Json -Compress; docker compose -p a02-direct logs --tail 5 api; docker compose -p a02-direct start redis")
    add(15,'Counter survives down and up',"$env:API_PORT='18004'; docker compose -p a02-direct down; docker compose -p a02-direct up -d --wait; $actual=(Invoke-RestMethod http://localhost:18004/stats).predictions; $expected=[int](Get-Content evidence/direct-count.txt); Write-Output \"Persisted: $actual; expected: $expected\"; if($actual -ne $expected){exit 1}")
    add(15,'Removing the volume resets the counter',"$env:API_PORT='18004'; docker compose -p a02-direct down -v; docker compose -p a02-direct up -d --wait; Invoke-RestMethod http://localhost:18004/stats | ConvertTo-Json; docker compose -p a02-direct ps")
elif phase=='registry':
    add(16,'Public Docker Hub release tags and digests',"$a=Invoke-RestMethod https://hub.docker.com/v2/repositories/asad3390/breast-cancer-triage-api/tags/1.0.0; $b=Invoke-RestMethod https://hub.docker.com/v2/repositories/asad3390/breast-cancer-triage-api/tags/latest; $a,$b | Select-Object name,digest,full_size | Format-List; if($a.digest -ne $b.digest){exit 1}")
    add(16,'Push both verified release tags','docker tag asad3390/breast-cancer-triage-api:1.0.0 asad3390/breast-cancer-triage-api:latest; if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }; docker push asad3390/breast-cancer-triage-api:1.0.0; if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }; docker push asad3390/breast-cancer-triage-api:latest',build=True)
    add(17,'Published stack and matching image digest',"docker compose -f ../clean-room/docker-compose.hub.yml ps; Get-ChildItem ../clean-room -Force | Select-Object Name; docker image inspect --format '{{json .RepoDigests}}' asad3390/breast-cancer-triage-api:1.0.0; python scripts/probe_api.py")
    add(17,'Remove assignment images and verify anonymous clean-room pull','python scripts/cleanroom_live.py')

execute(jobs[options.skip:])
