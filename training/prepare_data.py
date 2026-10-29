"""Export the bundled dataset; v2 removes the final 30 rows deterministically."""
import argparse
from pathlib import Path
from sklearn.datasets import load_breast_cancer

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--version', type=int, choices=[1, 2], default=1)
    args = parser.parse_args()
    data = load_breast_cancer(as_frame=True).frame
    data.columns = [name.replace(' ', '_') for name in data.columns]
    if args.version == 2:
        data = data.iloc[:-30].copy()
    assert len(data.columns) - 1 == 30
    assert not data.isnull().any().any()
    path = Path('data/raw/breast_cancer.csv')
    path.parent.mkdir(parents=True, exist_ok=True)
    data.to_csv(path, index=False, lineterminator='\n')
    print(f'Version {args.version}: {len(data)} rows, 30 features, no nulls; {path.stat().st_size} bytes')

if __name__ == '__main__':
    main()
