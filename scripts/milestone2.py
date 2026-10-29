import json
from evidence import ROOT, run, py

run(7, ['python', '-m', 'training.train'])
run(8, ['dvc', 'repro'])
run(8, ['dvc', 'repro'])
py(8, "from pathlib import Path; p=Path('params.yaml'); p.write_text(p.read_text().replace('n_estimators: 150', 'n_estimators: 160')); print('Changed forest.n_estimators from 150 to 160')")
run(8, ['dvc', 'repro'])
run(8, ['dvc', 'push'])
py(9, "import csv,json; from pathlib import Path; row=next(csv.DictReader(open('data/raw/breast_cancer.csv'))); p={k:float(v) for k,v in row.items() if k!='target'}; Path('sample.json').write_text(json.dumps(p,indent=2)); print('Created sample.json with',len(p),'numeric features')")
run(9, ['python', '-m', 'pytest', '-q', 'tests'])
run(9, ['git', 'add', 'training', 'app', 'tests', 'requirements-train.txt', 'requirements-serve.txt', 'requirements-dev.txt', 'params.yaml', 'dvc.yaml', 'dvc.lock', 'metrics.json', 'sample.json', 'dvc-remote', 'scripts/milestone2.py'])
run(9, ['git', 'commit', '-m', 'Milestone 2: reproducible model selection, DVC pipeline and validated FastAPI service'])
