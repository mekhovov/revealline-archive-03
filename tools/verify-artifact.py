#!/usr/bin/env python3
"""No HTTP: check all uploaded bytes and the finite hidden-file set immediately before upload."""
import argparse,json
from pathlib import Path
from prepare import REPO,H,require,scan,verify_directories
p=argparse.ArgumentParser();p.add_argument('artifact');a=p.parse_args()
lock=json.loads((REPO/'source-lock.json').read_text());raw=(REPO/'expected-inventory.json').read_bytes()
require(H(raw)==lock['expectedInventorySha256'],'Inventory pin changed');expected=json.loads(raw)
actual=scan(Path(a.artifact).resolve())
require(actual==expected['files'],'Missing, changed or extra artifact bytes')
verify_directories(Path(a.artifact).resolve(),expected['files'])
require(len(actual)==expected['fileCount'] and sum(r['bytes'] for r in actual)==expected['totalBytes']<=800_000_000,'Count/byte budget mismatch')
require(sorted(r['path'] for r in actual if any(c.startswith('.') for c in r['path'].split('/')))==expected['hiddenFiles'],'Unexpected hidden file')
print(json.dumps({'passed':True,'fileCount':len(actual),'totalBytes':expected['totalBytes'],'hiddenFiles':expected['hiddenFiles'],'expectedInventorySha256':H(raw)}))
