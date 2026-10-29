import json
from evidence import ROOT, run, py

if not (ROOT/'.git').exists():
    run(5, ['git', 'init', '-b', 'main'])
    run(5, ['git', 'config', 'user.name', 'Assignment Student'])
    run(5, ['git', 'config', 'user.email', 'student@localhost'])
    run(5, ['git', 'add', '.gitignore', '.dvcignore', 'scripts/evidence.py', 'scripts/milestone0.py'])
    run(5, ['git', 'commit', '-m', 'Milestone 0: record Docker CLI exercise workflow'])
run(5, ['git', 'config', 'core.autocrlf', 'false'])
run(5, ['python', '-m', 'training.prepare_data', '--version', '1'])
run(5, ['dvc', 'init', '--force'])
run(5, ['dvc', 'add', 'data/raw/breast_cancer.csv'])
run(5, ['dvc', 'remote', 'add', '-d', 'localstore', 'dvc-remote'])
run(5, ['dvc', 'push'])
run(5, ['git', 'add', '.dvc', '.dvcignore', 'data/raw/.gitignore', 'data/raw/breast_cancer.csv.dvc', 'dvc-remote', 'training/prepare_data.py', 'training/__init__.py', 'scripts/milestone1.py'])
run(5, ['git', 'commit', '-m', 'Milestone 1: track original 569-row dataset and portable DVC remote'])
run(5, ['git', 'tag', 'data-v1'])
run(5, ['git', 'ls-files', 'data/raw'])
py(5, "from pathlib import Path; Path('data/raw/breast_cancer.csv').unlink(); print('Removed working CSV to demonstrate dvc pull restore')")
run(5, ['dvc', 'pull', 'data/raw/breast_cancer.csv.dvc'])
table = []
def snapshot(version):
    import yaml
    path = ROOT/'data/raw/breast_cancer.csv'
    commit = run(6, ['git', 'rev-parse', 'HEAD']).strip()
    pointer = yaml.safe_load(path.with_suffix('.csv.dvc').read_text())['outs'][0]
    table.append({'version': version, 'git_commit': commit, 'dvc_hash': pointer['md5'], 'rows': len(path.read_text().splitlines())-1, 'bytes': path.stat().st_size})
snapshot('v1')
run(6, ['python', '-m', 'training.prepare_data', '--version', '2'])
run(6, ['dvc', 'add', 'data/raw/breast_cancer.csv'])
run(6, ['dvc', 'push'])
run(6, ['git', 'add', 'data/raw/breast_cancer.csv.dvc', 'dvc-remote'])
run(6, ['git', 'commit', '-m', 'Milestone 1: version corrected dataset with final 30 rows removed'])
run(6, ['git', 'tag', 'data-v2'])
snapshot('v2')
run(6, ['git', 'checkout', 'data-v1', '--', 'data/raw/breast_cancer.csv.dvc'])
run(6, ['dvc', 'checkout', 'data/raw/breast_cancer.csv.dvc'])
py(6, "import pandas as pd; n=len(pd.read_csv('data/raw/breast_cancer.csv')); print('Restored v1 rows:', n); assert n==569")
run(6, ['git', 'checkout', 'data-v2', '--', 'data/raw/breast_cancer.csv.dvc'])
run(6, ['dvc', 'checkout', 'data/raw/breast_cancer.csv.dvc'])
py(6, "import pandas as pd; n=len(pd.read_csv('data/raw/breast_cancer.csv')); print('Restored v2 rows:', n); assert n==539")
(ROOT/'evidence/dataset_versions.json').write_text(json.dumps(table, indent=2))
