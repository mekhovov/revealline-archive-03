# RevealLine archive 03

This publication candidate prepares unchanged **v0.33.0 and v0.34.0** for `mekhovov/revealline-archive-03`. One local frozen-site reuse assembly and complete artifact verification have passed. Hosted rebuilding, deployment and canonical browser acceptance remain separate gates. Main allocation stays unchanged until canonical acceptance.

The nine infrastructure files derive from the accepted Archive02 v0.32 expansion, reviewed candidate `ac7c07e775fe4f014905d8fb9fc4a442d8203a05`. Archive01 and Archive02 allocation entries remain unchanged. The candidate allocation appends only Archive03 and these two editions. Original game files, media, version identifiers, saved and earned artwork identities, releases and tag objects are preserved. ZIP downloads remain on the original `mekhovov/revealline` GitHub Releases.

## Exact authority and capacity

- Controller source: `fb6a199a4617554d51fa3f9fe9968754244543eb`, current version v0.36.0. It is the tested and locally frozen source; v0.36 public delivery is a separate gate.
- All **43 semantic release records** retain their exact raw bytes, tag objects and peeled commits. The complete **44-tag set** also includes the historical nonsemantic motion-lab tag. Any change requires a new review.
- v0.33.0: source `e29f2ac9207b047c07e6b72f94fa24cea9b00e1c`; **254 canonical files / 148,205,393 bytes**.
- v0.34.0: source `ef1cc41553b7f8c4b1de0156b7921569b0d71f60`; **265 canonical files / 160,221,565 bytes**.
- Verified local artifact: **524 files / 308,441,778 bytes**, leaving **491,558,222 bytes** below the unchanged **800,000,000-byte** archive cap. The locally assembled artifact matches the independently derived inventory exactly. Local preparation reused verified frozen sites; it did not rerun the two archived CLIs.
- Three hidden files: `.nojekyll` and the two original `.xonix-build.json` ownership markers.
- Expected inventory SHA256: `dc1eb39fafeb5aab0dda962cf70917b04e5c6174d307988fbcc588222749f886`.
- Source lock SHA256: `f2a2667153f38357dc0561d1c9d5a9392c8c5d7cfc4f10472b89ff1007ec7379`.
- Candidate allocation SHA256: `29d9d2d27ab2346903dc438ea36cf8f0d5745b7b36de7e7f557d2beb061bdfc0`. The controller's unchanged original allocation is `f82060fd3efccbf593961d3923cdeae9be0e04484bcd2b19c115dbc34a277a1a`.

The 519 canonical entries are copied exactly from the accepted v0.36 local Pages inventory `0335c2a4af69e74ff3ee0de7376462551004b9828b177e60698d7a90e9b2390a`; they include two release records, checksum sidecars and ownership markers. The redundant ZIP bodies are excluded from Pages. Independent fixed templates derive only five global files totaling 14,820 bytes: `.nojekyll`, `index.html`, `archive-routing.json`, and `releases/index.html` / `releases/index.json`. The earlier planning estimate of 522 files omitted two global files; the original proposal remains preserved and the corrected count is **524**.

Archive03 has no prior public archive inventory. `priorArchiveInventorySha256` is explicitly null. Canonical preservation is compared with the original frozen editions and the accepted main inventory. The archive index lists two editions with latest hosted v0.34.0; routing describes all 43 release records and the candidate allocation's 41 archived editions across three shards.

## Reproduction contract

`tools/prepare.py` requires Node 22.22.2, the exact controller Git files, all locked tag objects and peeled release commits, pinned allocation and inventory, and an absent output directory. A small metadata guard rejects a mismatched Archive03 repository, selected edition set, controller version/source, history set or increased budget. It runs before any source extraction or game build.

The hosted default remains the accepted archived-CLI pipeline: freshly archive each selected source commit, verify its frozen TAR hash and embedded commit, safely extract every bounded ordinary member, compare Git blobs and modes, and invoke that edition's own original CLI. Both manifest and ZIP hashes, complete ZIP member/CRC/body checks, loose bytes, checksums, ownership files and complete expected public inventory must pass. The source controller assembles the verified sites. All 43 exact release records are staged before `buildPages` runs, preventing missing-record release creation fallback. Only the two selected sites are materialized.

The optional local `--reuse-frozen-sites` mode requires `--frozen-root`. It compares the original TAR against a fresh Git archive stream and its exact frozen hash, then validates bounded TAR members against Git blobs and modes without creating another extracted source. It copies the existing sites and performs the same full manifest, ZIP, loose-body, canonical-inventory and post-run checks. This mode verifies frozen outputs; it does not claim a fresh archived-CLI build. The hosted workflow uses the default two CLI builds.

All original directory, symlink, special-file, traversal, extra-file, empty-directory, hash, CRC, tag-preservation and frozen-tree-preservation checks remain. Failed attempts are retained. The workflow preserves pinned upload-pages-artifact v5, explicit hidden-file inclusion, read-only checkout credentials and the accepted checkout/setup/deploy action versions.

```sh
# After source review and a separate capacity/execution admission, with Node 22.22.2 on PATH:
PYTHONDONTWRITEBYTECODE=1 /usr/bin/python3 archive/tools/test-verify.py
/usr/bin/python3 archive/tools/prepare.py --git-root source --builder-source source --out /absolute/new/archive03
/usr/bin/python3 archive/tools/verify-artifact.py /absolute/new/archive03/artifact
```

For local reuse, append `--frozen-root /absolute/original/releases --reuse-frozen-sites`. Use an absolute Python interpreter and verify the child Node version; local runtime shims previously selected a different Node version and correctly caused refusal. The workflow's Ubuntu runner uses its setup-node environment and ordinary Python.

## Remaining acceptance gates

1. Preserve the reviewed nine-file source, 22 passing bounded guard tests, and completed local reuse evidence. The one local assembly and subsequent artifact verifier matched all 524 files, all 519 canonical entries, both original manifest/ZIP bodies, and unchanged selected frozen trees and 44 tag objects. The exact controller was extracted from its retained frozen TAR; no additional TAR copy or archived CLI rebuild was needed. Independent receipt review accompanies this publication candidate.
2. Publish through a reviewed feature PR and hosted deployment. Archive03 publication may precede v0.36 delivery because these two older editions and their frozen originals are already verified. Require successful default archived-CLI builds and complete artifact verification; preserve all original game tags. The feature PR must be reviewed before merge.
3. Audit all **524** canonical paths and reconcile all **519** original canonical hashes. Retain failed requests. Root separately verifies both native canonical journeys, explicit Continue, win/Collection, original artwork and query/fragment preservation.
4. Only after canonical acceptance may a successor main source adopt the candidate allocation. Validate main bridge and retirement-worker regressions, normal old-prefix worker transition, existing saved and earned contexts, and exact final Pages admission under **950,000,000 bytes**. Do not force worker takeover, erase caches or player data, or rewrite historical games.

Historical archive preparation timeouts and legacy media warnings remain recorded with their original scope; identical archived bytes do not imply those behaviors were repaired. Online, offline preparation, cold launch and disconnected-network behavior need separate evidence. Missing originals in an existing user profile must remain distinguishable from transport or archive damage. No public/offline, physical controller, phone or historical installer success is claimed by the local preparation or publication candidate. Installed-pack, managed-media and offline budgets are unchanged.

Local reuse handoff SHA256: `0077e278df4f4a706a307217ad39eacf70e896357784de0369de88e45ca4cc48`. Source review SHA256: `90d7d8b2eef640f2a3e7f30d7055f2f2d8c8c7137db5d2131fb8b9b5e00607e1`. These local receipts preserve the full command, inventory and preservation chain; they are evidence of local verification, not a hosted rebuild or public acceptance.
