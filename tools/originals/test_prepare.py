"""Tiny local cohorts: no release downloads, game builds or network access."""
import copy
import hashlib
from html.parser import HTMLParser
import json
from pathlib import Path
import subprocess
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from prepare import MIN_FREE_BYTES, prepare
from verify import LIMIT, ROOT, digest, locked_inputs, metadata_inventory, verify


def encoded(value):
    return (json.dumps(value, indent=2) + '\n').encode()


def sha(value):
    return hashlib.sha256(value).hexdigest()


def git(directory, *args):
    return subprocess.check_output(['git', '-C', str(directory), *args], stderr=subprocess.DEVNULL, text=True).strip()


def init(directory):
    directory.mkdir()
    git(directory, 'init', '-q')
    git(directory, 'config', 'user.name', 'Archive fixture')
    git(directory, 'config', 'user.email', 'fixture@example.invalid')


# Exercises the real orchestration/subprocess protocol, not ZIP integrity.
# The production workflow separately runs the pinned extractor's ZIP tests.
EXTRACTOR = '''import argparse, json, pathlib, subprocess
p=argparse.ArgumentParser()
for name in ('metadata','output','receipt'): p.add_argument('--'+name,required=True)
a=p.parse_args(); m=pathlib.Path(a.metadata); out=pathlib.Path(a.output)
r=json.loads((m/'release.json').read_bytes())
BEHAVIOR
out.mkdir(); (out/'body.txt').write_text(r['version'])
(out/'manifest.json').write_bytes((m/'manifest.json').read_bytes())
(out/'distribution.zip.sha256').write_bytes((m/'distribution.zip.sha256').read_bytes())
(out/'.xonix-build.json').write_text('{\\n  "tool": "xonix-game-cli",\\n  "formatVersion": 1\\n}\\n')
pathlib.Path(a.receipt).write_text(json.dumps(dict(version=r['version'],gameSourceRevision=r['sourceRevision'],distributionSha256=r['distributionSha256'],manifestSha256=r['manifestSha256'],crcAndHashesVerified=True)))
'''


class CohortTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.base = Path(temp.name)
        self.source = self.base / 'source'
        self.archive = self.base / 'archive'
        self.output = self.base / 'output'

    def fixture(self, behavior='pass'):
        init(self.source)
        (self.source / 'extractor.py').write_text(EXTRACTOR.replace('BEHAVIOR', behavior))
        git(self.source, 'add', '.')
        git(self.source, 'commit', '-qm', 'local fixture')
        revision = git(self.source, 'rev-parse', 'HEAD')
        init(self.archive)
        (self.archive / 'index.html').write_bytes(b'fixture index')
        (self.archive / 'releases').mkdir()
        (self.archive / 'releases/index.html').write_bytes(b'fixture explorer')
        releases = []
        for version in ('v0.1.0', 'v0.2.0'):
            git(self.source, 'tag', '-a', version, '-m', 'fixture')
            directory = self.archive / 'metadata' / version
            directory.mkdir(parents=True)
            manifest = {'version': version, 'sourceRevision': revision, 'totalBytes': len(version), 'files': [{'path': 'body.txt', 'bytes': len(version), 'sha256': sha(version.encode())}]}
            manifest_bytes = encoded(manifest)
            record = {'version': version, 'sourceRevision': revision, 'distributionSha256': sha(version.encode()), 'manifestSha256': sha(manifest_bytes)}
            (directory / 'release.json').write_bytes(encoded(record))
            (directory / 'manifest.json').write_bytes(manifest_bytes)
            (directory / 'distribution.zip.sha256').write_text(record['distributionSha256'] + '  distribution.zip\n')
            releases.append({**{key: record[key] for key in ('version', 'sourceRevision', 'distributionSha256')}, 'tagObject': git(self.source, 'rev-parse', 'refs/tags/' + version), 'metadata': {name: digest(directory / name) for name in ('release.json', 'manifest.json', 'distribution.zip.sha256')}})
        self.lock = {'format': 'revealline-archive-originals.v2', 'archiveId': 'fixture', 'toolingCommit': revision, 'extractorPath': 'extractor.py', 'extractorSha256': digest(self.source / 'extractor.py'), 'releases': releases, 'budgetBytes': LIMIT}
        rows = [row for release in releases for row in metadata_inventory(self.archive, release)]
        rows += [{'path': 'index.html', 'bytes': 13, 'sha256': sha(b'fixture index')}, {'path': '.nojekyll', 'bytes': 0, 'sha256': sha(b'')}]
        rows.append({'path': 'releases/index.html', 'bytes': 16, 'sha256': sha(b'fixture explorer')})
        rows.sort(key=lambda row: row['path'])
        self.expected = {'base': 'https://example.invalid/', 'files': rows}
        (self.archive / 'expected-inventory.json').write_bytes(encoded(self.expected))
        self.lock.update(expectedInventorySha256=digest(self.archive / 'expected-inventory.json'), expectedFiles=len(rows), expectedBytes=sum(row['bytes'] for row in rows))
        self.write_lock()
        git(self.archive, 'add', '.')
        git(self.archive, 'commit', '-qm', 'local metadata fixture')

    def write_lock(self):
        (self.archive / 'source-lock.json').write_bytes(encoded(self.lock))

    def assemble(self):
        with patch('prepare.shutil.disk_usage', return_value=SimpleNamespace(free=MIN_FREE_BYTES)):
            return prepare(self.source, self.output, self.archive)

    def test_two_original_cohorts_and_independent_artifact_reread(self):
        self.fixture()
        result = self.assemble()
        self.assertEqual(result['status'], 'PASS')
        self.assertEqual([r['version'] for r in result['releases']], ['v0.1.0', 'v0.2.0'])
        self.assertEqual(result['files'], 13)
        self.assertEqual((self.output / 'artifact/releases/index.html').read_bytes(), b'fixture explorer')
        self.assertEqual(verify(self.output / 'artifact', self.expected['files'])['bytes'], result['bytes'])
        for version in ('v0.1.0', 'v0.2.0'):
            self.assertEqual((self.output / 'artifact/releases' / version / 'release.json').read_bytes(), (self.archive / 'metadata' / version / 'release.json').read_bytes())
            self.assertTrue((self.output / ('zip-receipt-' + version + '.json')).is_file())

    def test_pinned_qualification_copied_without_changing_original_cohort(self):
        self.fixture()
        release = self.lock['releases'][1]
        tree = git(self.source, 'rev-parse', 'HEAD^{tree}')
        proof = {'format': 'revealline-source-qualification.v1', 'version': release['version'], 'sourceRevision': release['sourceRevision'], 'actualCheckoutCommit': release['sourceRevision'], 'sourceTree': tree, 'actualCheckoutTree': tree, 'passed': True, 'allTrackedSourceContentsAndModesMatch': True, 'gates': [{'gate': name, 'step': {'conclusion': 'success'}} for name in ['test', 'lint', 'format', 'native-format', 'validate', 'motion-syntax']]}
        source = self.archive / 'metadata/v0.2.0/source-qualification.json'
        source.write_bytes(encoded(proof))
        release['sourceTree'] = tree
        release['sourceQualification'] = {'bytes': source.stat().st_size, 'sha256': digest(source)}
        self.expected['files'].append({'path': 'releases/v0.2.0/source-qualification.json', 'bytes': source.stat().st_size, 'sha256': digest(source)})
        self.expected['files'].sort(key=lambda row: row['path'])
        (self.archive / 'expected-inventory.json').write_bytes(encoded(self.expected))
        self.lock.update(expectedInventorySha256=digest(self.archive / 'expected-inventory.json'), expectedFiles=len(self.expected['files']), expectedBytes=sum(row['bytes'] for row in self.expected['files']))
        self.write_lock()
        result = self.assemble()
        self.assertEqual(result['files'], 14)
        self.assertEqual((self.output / 'artifact/releases/v0.2.0/source-qualification.json').read_bytes(), source.read_bytes())
        self.assertEqual((self.output / 'artifact/releases/v0.1.0/site/body.txt').read_text(), 'v0.1.0')

    def test_capacity_refuses_before_output_or_source_access(self):
        with patch('prepare.shutil.disk_usage', return_value=SimpleNamespace(free=MIN_FREE_BYTES - 1)):
            with self.assertRaisesRegex(ValueError, '3 GiB'):
                prepare(self.source, self.output, self.archive)
        self.assertFalse(self.output.exists())

    def test_existing_output_is_never_overwritten(self):
        self.fixture()
        self.output.mkdir()
        sentinel = self.output / 'keep'
        sentinel.write_bytes(b'unchanged')
        with self.assertRaises(FileExistsError):
            self.assemble()
        self.assertEqual(list(self.output.iterdir()), [sentinel])
        self.assertEqual(sentinel.read_bytes(), b'unchanged')

    def test_bad_second_metadata_refuses_before_first_extraction(self):
        self.fixture()
        (self.archive / 'metadata/v0.2.0/release.json').write_bytes(b'changed')
        with self.assertRaisesRegex(ValueError, 'metadata bytes changed'):
            self.assemble()
        self.assertFalse(self.output.exists())

    def test_missing_release_explorer_bridge_refuses_before_extraction(self):
        self.fixture()
        (self.archive / 'releases/index.html').unlink()
        with self.assertRaises(FileNotFoundError):
            self.assemble()
        self.assertFalse(self.output.exists())

    def test_inventory_cannot_omit_the_release_explorer_route(self):
        self.fixture()
        self.expected['files'] = [r for r in self.expected['files'] if r['path'] != 'releases/index.html']
        (self.archive / 'expected-inventory.json').write_bytes(encoded(self.expected))
        self.lock.update(expectedInventorySha256=digest(self.archive / 'expected-inventory.json'), expectedFiles=len(self.expected['files']), expectedBytes=sum(r['bytes'] for r in self.expected['files']))
        self.write_lock()
        with self.assertRaisesRegex(ValueError, 'Canonical inventory'):
            self.assemble()
        self.assertFalse(self.output.exists())

    def test_duplicate_version_and_cohort_inventory_omission_refuse(self):
        self.fixture()
        original = copy.deepcopy(self.lock)
        self.lock['releases'].append(copy.deepcopy(self.lock['releases'][0]))
        self.write_lock()
        with self.assertRaisesRegex(ValueError, 'Duplicate'):
            self.assemble()
        self.lock = original
        self.lock['releases'].pop()
        self.write_lock()
        with self.assertRaisesRegex(ValueError, 'Canonical inventory'):
            self.assemble()
        self.assertFalse(self.output.exists())

    def test_manifest_source_disagreement_refuses_even_with_rehashed_pin(self):
        self.fixture()
        release = self.lock['releases'][1]
        manifest_path = self.archive / 'metadata/v0.2.0/manifest.json'
        manifest = json.loads(manifest_path.read_bytes())
        manifest['sourceRevision'] = '0' * 40
        manifest_path.write_bytes(encoded(manifest))
        release['metadata']['manifest.json'] = digest(manifest_path)
        with self.assertRaisesRegex(ValueError, 'manifest identity'):
            metadata_inventory(self.archive, release)

    def test_second_extraction_failure_cannot_emit_combined_success(self):
        self.fixture("if r['version']=='v0.2.0': raise ValueError('fixture second failure')")
        with self.assertRaises(subprocess.CalledProcessError):
            self.assemble()
        self.assertTrue((self.output / 'zip-receipt-v0.1.0.json').is_file())
        self.assertFalse((self.output / 'receipt.json').exists())

    def test_mismatched_extraction_receipt_cannot_emit_combined_success(self):
        self.fixture("r['distributionSha256']='0'*64")
        with self.assertRaisesRegex(ValueError, 'extraction receipt identity'):
            self.assemble()
        self.assertTrue((self.output / 'zip-receipt-v0.1.0.json').is_file())
        self.assertFalse((self.output / 'zip-receipt-v0.2.0.json').exists())
        self.assertFalse((self.output / 'receipt.json').exists())

    def test_tag_identity_changed_before_or_during_extraction_refuses(self):
        self.fixture("if r['version']=='v0.2.0': subprocess.run(['git','-C',str(pathlib.Path(__file__).parent),'tag','-d','v0.1.0'],check=True,stdout=subprocess.DEVNULL)")
        with self.assertRaises(subprocess.CalledProcessError):
            self.assemble()
        self.assertFalse((self.output / 'receipt.json').exists())
        self.output = self.base / 'next-output'
        with self.assertRaises(subprocess.CalledProcessError):
            self.assemble()
        self.assertFalse(self.output.exists())

    def test_changed_extracted_body_fails_full_inventory(self):
        self.fixture()
        result = self.assemble()
        body = self.output / 'artifact/releases/v0.2.0/site/body.txt'
        body.write_bytes(b'corrupt')
        with self.assertRaisesRegex(ValueError, 'missing, extra or changed'):
            verify(self.output / 'artifact', self.expected['files'])
        self.assertTrue(result['noHistoricalBuilds'])

    def add_static_routes(self):
        self.lock['staticFiles'] = []
        for name, body in [('archive-routing.json', b'{"retained":"routing"}\n'), ('releases/index.json', b'{"retained":"index"}\n')]:
            target = self.archive / 'static' / name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(body)
            row = {'path': name, 'bytes': len(body), 'sha256': sha(body)}
            self.lock['staticFiles'].append(row)
            self.expected['files'].append(dict(row))
        self.expected['files'].sort(key=lambda row: row['path'])
        (self.archive / 'expected-inventory.json').write_bytes(encoded(self.expected))
        self.lock.update(expectedInventorySha256=digest(self.archive / 'expected-inventory.json'), expectedFiles=len(self.expected['files']), expectedBytes=sum(row['bytes'] for row in self.expected['files']))
        self.write_lock()

    def test_preserved_static_routes_are_copied_and_independently_verified(self):
        self.fixture()
        self.add_static_routes()
        result = self.assemble()
        self.assertEqual(result['files'], 15)
        for row in self.lock['staticFiles']:
            self.assertEqual((self.output / 'artifact' / row['path']).read_bytes(), (self.archive / 'static' / row['path']).read_bytes())
        (self.output / 'artifact/releases/index.json').write_bytes(b'changed after copy')
        with self.assertRaisesRegex(ValueError, 'missing, extra or changed'):
            verify(self.output / 'artifact', self.expected['files'])

    def test_changed_static_original_refuses_before_any_extraction(self):
        self.fixture()
        self.add_static_routes()
        (self.archive / 'static/archive-routing.json').write_bytes(b'corrupt original')
        with self.assertRaisesRegex(ValueError, 'static route bytes changed'):
            self.assemble()
        self.assertFalse(self.output.exists())

    def test_unreviewed_static_path_duplicate_and_symlink_refuse(self):
        self.fixture()
        self.add_static_routes()
        original = copy.deepcopy(self.lock['staticFiles'])
        for name in ('../escape.json', 'index.html', 'releases/v0.1.0/site/body.txt'):
            with self.subTest(path=name):
                self.lock['staticFiles'] = [dict(original[0], path=name)]
                self.write_lock()
                with self.assertRaises(ValueError): self.assemble()
                self.assertFalse(self.output.exists())
        self.lock['staticFiles'] = [original[0], original[0]]
        self.write_lock()
        with self.assertRaisesRegex(ValueError, 'duplicate'):
            self.assemble()
        self.lock['staticFiles'] = original
        self.write_lock()
        path = self.archive / 'static/archive-routing.json'
        body = path.read_bytes()
        path.unlink()
        target = self.archive / 'original-routing.json'
        target.write_bytes(body)
        path.symlink_to(target)
        with self.assertRaisesRegex(ValueError, 'static route bytes changed'):
            self.assemble()
        self.assertFalse(self.output.exists())

    def test_static_route_cannot_be_dropped_even_with_rehashed_inventory(self):
        self.fixture()
        self.add_static_routes()
        self.expected['files'] = [row for row in self.expected['files'] if row['path'] != 'archive-routing.json']
        (self.archive / 'expected-inventory.json').write_bytes(encoded(self.expected))
        self.lock.update(expectedInventorySha256=digest(self.archive / 'expected-inventory.json'), expectedFiles=len(self.expected['files']), expectedBytes=sum(row['bytes'] for row in self.expected['files']))
        self.write_lock()
        with self.assertRaisesRegex(ValueError, 'Canonical inventory'):
            self.assemble()
        self.assertFalse(self.output.exists())


class CommittedMetadataTests(unittest.TestCase):
    def test_exact_three_legacy_cohorts_and_v0602_metadata(self):
        lock, inventory = locked_inputs(ROOT)
        self.assertEqual((lock['expectedFiles'], lock['expectedBytes']), (1490, 783088453))
        self.assertEqual([r['version'] for r in lock['releases']], ['v0.33.0', 'v0.34.0', 'v0.35.0', 'v0.60.2'])
        legacy = json.loads((ROOT / 'legacy/source-lock.v1.json').read_bytes())
        self.assertEqual(legacy['format'], 'revealline-archive-source-lock.v1')
        self.assertEqual(legacy['archiveBudgetBytes'], LIMIT)
        for cohort in lock['releases'][:3]:
            old = next(record for record in legacy['releases'] if record['version'] == cohort['version'])
            self.assertEqual(cohort['sourceRevision'], old['commit'])
            self.assertEqual(cohort['tagObject'], old['tagObject'])
            self.assertEqual((ROOT / 'metadata' / cohort['version'] / 'release.json').read_bytes(), old['recordUtf8'].encode())
        original = json.loads((ROOT / 'legacy/expected-inventory.v1.json').read_bytes())
        self.assertEqual(len(original['files']), 803)
        actual = {row['path']: row for row in inventory['files']}
        self.assertEqual([actual[row['path']] for row in original['files']], original['files'])
        successor = lock['releases'][3]
        self.assertEqual(successor['tagObject'], '632bf35908ea33fb9356d41d758d302f19361c12')
        self.assertEqual(successor['sourceRevision'], 'ece40093940aabdc3b3659a07394b856f33ad4a1')
        self.assertEqual(successor['sourceTree'], '32b36e6e8fc605911b2cb98cd8f67c97b8f4e214')
        self.assertEqual(successor['sourceQualification'], {'bytes': 71249, 'sha256': 'b56a5c5ee65e498671e1e296cddc816c6949488f476a5543cbac16e3d70de94f'})
        self.assertEqual(len([row for row in inventory['files'] if row['path'].endswith('/source-qualification.json')]), 1)

    def test_changed_or_wrong_identity_qualification_refuses(self):
        import shutil
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            shutil.copytree(ROOT / 'metadata', root / 'metadata')
            original = json.loads((ROOT / 'source-lock.json').read_bytes())['releases'][3]
            path = root / 'metadata/v0.60.2/source-qualification.json'
            data = path.read_bytes()
            for change in ('bytes', 'source', 'gates'):
                with self.subTest(change=change):
                    release = copy.deepcopy(original)
                    proof = json.loads(data)
                    if change == 'bytes':
                        path.write_bytes(b'changed')
                    else:
                        if change == 'source': proof['actualCheckoutCommit'] = '0' * 40
                        if change == 'gates': proof['gates'].pop()
                        path.write_bytes(encoded(proof))
                        release['sourceQualification'] = {'sha256': digest(path), 'bytes': path.stat().st_size}
                    with self.assertRaisesRegex(ValueError, 'qualification'):
                        metadata_inventory(root, release)
                    path.write_bytes(data)

    def test_legacy_routes_remain_exact_and_cannot_be_missing(self):
        lock, inventory = locked_inputs(ROOT)
        expected = json.loads((ROOT / 'legacy/expected-inventory.v1.json').read_bytes())
        lookup = {row['path']: row for row in expected['files']}
        for name in ('index.html', 'releases/index.html'):
            self.assertEqual(digest(ROOT / name), lookup[name]['sha256'])
        for row in lock['staticFiles']:
            self.assertEqual(row, lookup[row['path']])
            self.assertEqual(digest(ROOT / 'static' / row['path']), row['sha256'])


if __name__ == '__main__':
    unittest.main()
