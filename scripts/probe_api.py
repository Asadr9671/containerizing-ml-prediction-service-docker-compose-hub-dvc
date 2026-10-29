import argparse
import json
from pathlib import Path
import urllib.request
import urllib.error

parser = argparse.ArgumentParser()
parser.add_argument('--url', default='http://localhost:8000')
parser.add_argument('--threshold', type=float, default=0.5)
args = parser.parse_args()
for path in ['/health', '/model/info', '/stats']:
    response = urllib.request.urlopen(args.url+path)
    body = json.load(response)
    print('GET', path, response.status, json.dumps(body))
    if path == '/model/info':
        assert body['model_version']=='1.0.0'
        assert body['decision_threshold']==args.threshold
        assert body['metrics']['malignant_recall']>=0.95
request = urllib.request.Request(args.url+'/predict', data=Path('sample.json').read_bytes(), headers={'Content-Type':'application/json'})
response = urllib.request.urlopen(request)
body = json.load(response)
print('POST /predict', response.status, json.dumps(body))
assert body['threshold']==args.threshold
try:
    urllib.request.urlopen(urllib.request.Request(args.url+'/predict', data=b'{}', headers={'Content-Type':'application/json'}))
except urllib.error.HTTPError as error:
    print('POST /predict missing fields:', error.code)
    assert error.code==422
else:
    raise AssertionError('Missing fields were accepted')
