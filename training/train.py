"""Select by training-only CV malignant recall; evaluate untouched holdout."""
import argparse
import json
import os
import time
from pathlib import Path
import joblib
import numpy as np
import pandas as pd
import sklearn
import yaml
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, make_scorer, recall_score, roc_auc_score
from sklearn.model_selection import StratifiedKFold, cross_validate, train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

def malignant_auc(estimator, X, y):
    index = list(estimator.classes_).index(0)
    return roc_auc_score(np.asarray(y) == 0, estimator.predict_proba(X)[:, index])

def main():
    started = time.perf_counter()
    parser = argparse.ArgumentParser()
    parser.add_argument('--data-path', default='data/raw/breast_cancer.csv')
    parser.add_argument('--output-dir', default='artifacts')
    parser.add_argument('--model-version', default=None)
    args = parser.parse_args()
    params = yaml.safe_load(Path('params.yaml').read_text())
    seed = params['seed']
    if seed != 42:
        raise ValueError('Assignment requires seed 42')
    data = pd.read_csv(args.data_path)
    X, y = data.drop(columns='target'), data['target']
    if X.shape[1] != 30 or data.isnull().any().any():
        raise ValueError('Expected 30 features and no null values')
    train_x, test_x, train_y, test_y = train_test_split(
        X.to_numpy(), y.to_numpy(), test_size=params['test_size'], stratify=y, random_state=seed)
    cv = StratifiedKFold(n_splits=params['cv_folds'], shuffle=True, random_state=seed)
    models = {
        'logistic_regression': Pipeline([('scale', StandardScaler()), ('model', LogisticRegression(random_state=seed, **params['logistic']))]),
        'random_forest': Pipeline([('scale', StandardScaler()), ('model', RandomForestClassifier(random_state=seed, n_jobs=1, **params['forest']))]),
    }
    scoring = {'malignant_recall': make_scorer(recall_score, pos_label=0), 'accuracy': 'accuracy', 'roc_auc': malignant_auc}
    results = {}
    for name, model in models.items():
        scores = cross_validate(model, train_x, train_y, cv=cv, scoring=scoring)
        results[name] = {'cv': {key: float(scores['test_' + key].mean()) for key in scoring}}
    selected = max(results, key=lambda name: results[name]['cv']['malignant_recall'])
    # Selection is complete before any holdout metrics are computed.
    for name, model in models.items():
        model.fit(train_x, train_y)
        prediction = model.predict(test_x)
        results[name]['test'] = {'malignant_recall': float(recall_score(test_y, prediction, pos_label=0)),
                                 'accuracy': float(accuracy_score(test_y, prediction)),
                                 'roc_auc': float(malignant_auc(model, test_x, test_y))}
    print(json.dumps({'selected': selected, 'candidates': results}, indent=2))
    if results[selected]['test']['malignant_recall'] < 0.95:
        raise SystemExit('Quality gate FAILED: held-out malignant recall below 0.95')
    output = Path(args.output_dir)
    output.mkdir(parents=True, exist_ok=True)
    card = {'model_version': args.model_version or params['model_version'], 'model_family': selected,
            'feature_names': list(X.columns), 'feature_count': X.shape[1], 'seed': seed,
            'sklearn_version': sklearn.__version__, 'git_commit': os.getenv('GIT_SHA', 'local'),
            'decision_threshold': 0.5, 'metrics': results[selected]['test'], 'candidates': results,
            'dataset_rows': len(data), 'train_rows': len(train_y), 'test_rows': len(test_y)}
    joblib.dump(models[selected], output / 'model.joblib')
    (output / 'model_card.json').write_text(json.dumps(card, indent=2) + '\n')
    Path('metrics.json').write_text(json.dumps({'selected': selected, 'candidates': results}, indent=2) + '\n')
    print(f'Quality gate PASSED; training completed in {time.perf_counter()-started:.2f} seconds')

if __name__ == '__main__':
    main()
