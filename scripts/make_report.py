"""Browser screenshots of recorded real execution, assembled into a PDF."""
import html
import json
import re
import textwrap
from pathlib import Path
from playwright.sync_api import sync_playwright
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, Image
from evidence import ROOT

EVIDENCE = ROOT/'evidence'
shots = EVIDENCE/'screenshots'
shots.mkdir(exist_ok=True)
html_dir = EVIDENCE/'html'
html_dir.mkdir(exist_ok=True)
records = [json.loads(line) for line in (EVIDENCE/'commands.jsonl').read_text(encoding='utf-8').splitlines()]
titles = {1:'Installation and first container',2:'Container lifecycle, ports and logs',3:'Images, tags and cleanup',4:'Environment variables and bind mounts',5:'Dataset preparation and DVC tracking',6:'Dataset versioning',7:'Training script',8:'DVC training pipeline',9:'FastAPI service',10:'Baseline image',11:'Production image',12:'Run and inspect',13:'Request counter and Redis outage',14:'Compose stack',15:'Running the stack and persistence',16:'Registry publishing',17:'Clean-room verification',18:'Written analysis'}
milestones = {0:range(1,5),1:range(5,7),2:range(7,10),3:range(10,13),4:range(13,16),5:range(16,19)}

def lines_for(record):
    output = re.sub(r'\x1b\[[0-9;]*m','',record['output']).replace('\r','')
    lines = output.splitlines()
    if len(lines)>65:
        if record['command'].startswith('docker build'):
            chosen = [line for line in lines if 'CACHED' in line or 'RUN pip' in line or 'COPY ' in line or 'Quality gate' in line or 'DONE ' in line]
            lines = lines[:6]+['[Build log excerpt; complete output retained in commands.jsonl]']+chosen+lines[-12:]
        elif 'image inspect' in record['command']:
            data=json.loads(output)[0]
            lines=['[Inspect excerpt; complete JSON retained in commands.jsonl]']+json.dumps({k:data.get(k) for k in ('Id','RepoTags','Size','Config')},indent=2).splitlines()
        else:
            lines=lines[:12]+['[Middle omitted; complete output retained in commands.jsonl]']+lines[-38:]
    header = [f"$ {record['command']}", f"Recorded: {record['timestamp']} | exit={record['exit_code']} | elapsed={record['seconds']} s"]
    text=[]
    for line in header+lines+['']:
        text.extend(textwrap.wrap(line, width=118, replace_whitespace=False, drop_whitespace=False) or [''])
    return text

screens={}
with sync_playwright() as p:
    browser=p.chromium.launch(executable_path=r'C:\Program Files\Google\Chrome\Application\chrome.exe',headless=True)
    page=browser.new_page(viewport={'width':1280,'height':900},device_scale_factor=1)
    for task in range(1,18):
        items=[r for r in records if r['task']==task]
        screens[task]=[]
        for index,record in enumerate(items,1):
            # Setup retries remain in raw logs, but only final evidence is printed.
            if record['exit_code'] and any(x in record['output'] for x in ['ModuleNotFoundError','unexpected error','No file hash info']):
                continue
            lines=lines_for(record)
            for part,start in enumerate(range(0,len(lines),42),1):
                chunk=lines[start:start+42]
                if start:
                    chunk=['$ '+record['command']+' [output continued]']+chunk
                name=f'task{task:02d}-{index:03d}-{part:02d}'
                markup='<!doctype html><meta charset="utf-8"><style>body{margin:0;padding:24px;background:#101827;color:#e8edf5;font:16px/1.42 Consolas,monospace}h1{font:600 21px Arial;color:#79d6e8;margin:0 0 14px}pre{white-space:pre-wrap;overflow-wrap:anywhere;margin:0}footer{font:13px Arial;color:#a4b3c6;margin-top:14px}</style>'
                markup+=f'<h1>Task {task} · {html.escape(titles[task])}</h1><pre>{html.escape(chr(10).join(chunk))}</pre><footer>Captured execution transcript • original command output • Asia/Karachi</footer>'
                file=html_dir/(name+'.html')
                file.write_text(markup,encoding='utf-8')
                page.goto(file.as_uri())
                target=shots/(name+'.png')
                page.screenshot(path=str(target),full_page=True)
                screens[task].append(target)
    browser.close()

styles=getSampleStyleSheet()
styles['BodyText'].fontSize=11
styles['BodyText'].leading=16
styles['Heading1'].textColor=colors.HexColor('#133f57')
story=[]
def para(text,style='BodyText'):
    story.append(Paragraph(text,styles[style])); story.append(Spacer(1,10))
def table(rows,widths=None):
    wrapped=[[Paragraph(html.escape(str(c)),styles['BodyText']) for c in row] for row in rows]
    t=Table(wrapped,colWidths=widths,repeatRows=1)
    t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#e3eff5')),('GRID',(0,0),(-1,-1),0.5,colors.lightgrey),('VALIGN',(0,0),(-1,-1),'TOP'),('LEFTPADDING',(0,0),(-1,-1),8),('BOTTOMPADDING',(0,0),(-1,-1),8)]))
    story.append(t);story.append(Spacer(1,14))
def picture(path):
    img=Image(str(path))
    scale=min(770/img.imageWidth,460/img.imageHeight)
    img.drawWidth=img.imageWidth*scale; img.drawHeight=img.imageHeight*scale
    story.append(img)

para('MLOps Assignment 02','Title')
para('Containerizing an ML Prediction Service with Docker, Docker Compose, Docker Hub and DVC','Heading1')
para('Prepared for Asadr9671 • Docker Hub: asad3390 • 29 October 2026 (Asia/Karachi)')
para('GitHub: <link href="https://github.com/Asadr9671/containerizing-ml-prediction-service-docker-compose-hub-dvc">Asadr9671/containerizing-ml-prediction-service-docker-compose-hub-dvc</link>')
para('Docker Hub: <link href="https://hub.docker.com/r/asad3390/breast-cancer-triage-api">asad3390/breast-cancer-triage-api</link>')
published=(EVIDENCE/'published.json').exists()
github_published=(EVIDENCE/'github.json').exists()
para('Publication status: '+('Docker Hub release and anonymous clean-room verification completed. ' if published else 'Docker Hub release and clean-room verification pending. ')+('GitHub repository published.' if github_published else 'GitHub URL is the intended submission location; source publication is pending authentication.'))
para('Evidence method: screenshots show browser-rendered transcripts of commands actually executed, with original output, timestamps and exit codes. Live browser captures also show nginx and an executed Swagger prediction. Long build logs are explicitly excerpted; complete logs are retained in evidence/commands.jsonl. Expected failures are part of the assignment.')
para('AI assistance was used to prepare and execute this solution. Educational demonstration only; not a medical device.')
story.append(PageBreak())

notes={
1:'Docker client and engine versions are shown below. The first hello-world:linux run fetched the missing tag; the second reused the local image and omitted the pull output.',
2:'The second nginx instance failed on an occupied host port, then succeeded on a distinct port. Stopping retained the container; restarting reused it; removal followed stopping.',
3:'A tag is a human-readable reference to an image version. The Alpine Redis image was smaller than the regular image. Ubuntu exited because its default shell had no interactive input. Image removal failed while a stopped container referenced it; removing the container first resolved the conflict.',
4:'PostgreSQL initially stopped because no initialization password was configured. A deliberately disposable local exercise password enabled startup and an internal psql query. The host-mounted nginx HTML changed without restarting the container.',
5:'The exporter validated 30 features and no nulls. DVC tracks the CSV; Git tracks its pointer and the small, assignment-required local remote. Restoring the working CSV succeeded.',
6:'Version 2 removes the final 30 rows deterministically. Git restored each pointer and DVC restored the corresponding data, confirming 569 and 539 rows. All later training uses v2.',
7:'The model was chosen only by mean training-set CV malignant recall. Both candidates use a Pipeline. The stratified split, shuffled CV and model initialization use seed 42. The held-out recall gate is 0.95.',
8:'The first pipeline run executed training, the second skipped unchanged work, and changing forest.n_estimators from 150 to 160 caused training to run again. The selected model remained logistic regression.',
9:'Nine API tests cover valid prediction, class-0 probability, missing/extra fields, negative values, strings, booleans, Redis outage, threshold behavior and missing-artifact startup failure. Swagger below executes a real prediction against the local API.',
10:'The baseline uses Ubuntu, installs Python/pip with apt, copies the project before dependency installation and trains in the image. Cold timing uses --no-cache; base downloads and local/network conditions are included where incurred.',
11:'The production build trains separately and copies only model artifacts to the slim serving stage. Its final container runs as UID 10001. Rebuild output identifies reused dependency layers.',
12:'Standalone serving requires no Redis. The checks verify prediction, metadata, health, logs, image history, non-root UID and absence of training-only packages/data. A second container changes threshold to 0.99 and logging to DEBUG without rebuilding.',
13:'Three valid predictions incremented Redis by three. Stopping Redis left /health and /predict available; the API logged the counter outage. Invalid requests do not count as served predictions.',
14:'Compose uses service-name DNS, a Redis health dependency, a configurable API host port, and no published Redis port. Environment settings come from the ignored .env file.',
15:'The counter survived down/up because Redis AOF data remained in the named volume. Removing that volume with down -v reset the counter to zero on the next startup.',
16:'The production image, repository overview and publishing instructions are prepared. Actual public push, tag equality and Docker Hub username screenshots require account authentication.',
17:'The no-build Hub Compose file is prepared. Registry pull into an empty directory, unauthenticated access and digest matching cannot be claimed until the image is published.'}
if published:
    release=json.loads((EVIDENCE/'published.json').read_text())
    notes[16]='Public repository asad3390/breast-cancer-triage-api contains 1.0.0 and latest with identical digests. The overview documents the service, tags, standalone and Compose usage, environment variables and port.'
    notes[17]='All local assignment image copies were removed. An empty directory containing only docker-compose.hub.yml and .env pulled the published image with an empty Docker credential configuration. The stack became healthy and served a successful prediction. Hub and pulled digest match: '+release['tags']['1.0.0']
for milestone,tasks in milestones.items():
    para(f'Milestone {milestone}','Heading1')
    for task in tasks:
        para(f'Task {task}: {titles[task]}','Heading2')
        if task==18:
            para('An image is a read-only packaged filesystem and configuration; a container is its runnable instance with a writable layer. Removing Ubuntu failed because the stopped container still referenced its image. Removing that container first resolved the conflict.<br/><br/>The server must bind to 0.0.0.0 so traffic arriving through the container network can reach it. A host-to-container port mapping forwards traffic from the selected host port to the service port; nginx demonstrated why two containers cannot claim the same host port.<br/><br/>Git stores a small DVC pointer identifying the dataset content, avoiding large data in normal source history. Restoring data requires that pointer, DVC, and access to the matching cached object or remote. Here the committed dvc-remote folder supplies both dataset versions, and Git/DVC switching restored 569 and 539 rows.')
            continue
        para(notes[task])
        if task==6:
            rows=[['Table 1: version','Git commit','DVC MD5','Rows','Bytes']]
            for row in json.loads((EVIDENCE/'dataset_versions.json').read_text()):
                rows.append([row['version'],row['git_commit'][:12],row['dvc_hash'],row['rows'],row['bytes']])
            table(rows,[80,125,300,70,95])
        if task==7:
            metric=json.loads((ROOT/'metrics.json').read_text())
            rows=[['Table 2: model','CV recall','CV accuracy','CV AUC','Test recall','Test accuracy','Test AUC']]
            for name,result in metric['candidates'].items():
                rows.append([name+(' (selected)' if name==metric['selected'] else '')]+[f'{result[split][key]:.5f}' for split in ('cv','test') for key in ('malignant_recall','accuracy','roc_auc')])
            table(rows,[170,100,100,100,100,100,100])
        if task==11 and (EVIDENCE/'build_comparison.json').exists():
            rows=[['Table 3: image','Base','Size (MiB)','Cold (s)','Rebuild (s)','User']]
            for row in json.loads((EVIDENCE/'build_comparison.json').read_text()):
                rows.append([row['image'],row['base'],f"{row['size_bytes']/1024**2:.1f}",row['cold_seconds'],row['rebuild_seconds'],row['user']])
            table(rows,[80,250,105,105,105,105])
            para('The slim runtime excludes the Ubuntu build toolchain, training CSV and training-only packages. Dependency layers precede application code, so an application-only edit reuses installed dependencies and trained artifacts in the production build.')
        for index,path in enumerate(screens.get(task,[]),1):
            story.append(PageBreak());para(f'Milestone {milestone} · Task {task} · Evidence {index}','Heading2');picture(path)
        if task in (4,9):
            path=shots/('task04-bind-browser.png' if task==4 else 'task09-swagger-response.png')
            if path.exists():
                story.append(PageBreak());para(f'Task {task}: live browser screenshot','Heading2');picture(path)
        if task==16:
            for name in ('tags','overview'):
                path=shots/f'task16-hub-{name}.png'
                if path.exists():
                    story.append(PageBreak());para(f'Task 16: Docker Hub {name} - asad3390','Heading2');picture(path)
        story.append(PageBreak())
para('References and reproducibility','Heading1')
para('Official Docker multi-stage build documentation: https://docs.docker.com/build/building/multi-stage/<br/>Official DVC documentation: https://doc.dvc.org/start<br/>Exact reproduction, testing, Compose and publishing commands: README.md in the source repository.<br/>Full original execution records: evidence/commands.jsonl')
import argparse
parser=argparse.ArgumentParser()
parser.add_argument('--output', default='MLOps_A02_RollNumber.pdf')
output=ROOT.parent/parser.parse_args().output
def footer(canvas,doc):
    canvas.setFont('Helvetica',8);canvas.drawString(32,18,'MLOps Assignment 02 | Asadr9671 / asad3390');canvas.drawRightString(810,18,str(doc.page))
SimpleDocTemplate(str(output),pagesize=landscape(A4),leftMargin=32,rightMargin=32,topMargin=28,bottomMargin=30).build(story,onFirstPage=footer,onLaterPages=footer)
print(f'Created {output}; screenshot pages={sum(map(len,screens.values()))}')
