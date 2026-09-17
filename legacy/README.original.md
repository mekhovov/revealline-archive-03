# RevealLine archive 03 — proposed v0.35 extension

This candidate adds unchanged **v0.35.0** beside the already published v0.33.0 and v0.34.0. One bounded local frozen-site reuse assembly has passed with 22 guard tests, complete artifact verification and a zero-network HTTP preflight. A new hosted three-CLI build, deployment, actual HTTP audit, canonical v0.35 native acceptance and main routing change remain pending.

The existing Archive03 deployment is `1870c68ee5a05c60c55b3be2eb528fb035076207` (reviewed feature `c7b51766520bdfc28ef81ad0e03d512554cf9799`, identical tree). Its accepted HTTP receipt covers 524 files / 308,441,778 bytes. This extension preserves all **519 original canonical rows / 308,426,958 bytes**; only three generated global files change and 279 canonical v0.35 rows are added. `.nojekyll` and the root index remain exact.

## Exact proposed inventory

| Component                   |   Files |           Bytes |
| --------------------------- | ------: | --------------: |
| v0.33.0 canonical files     |     254 |     148,205,393 |
| v0.34.0 canonical files     |     265 |     160,221,565 |
| v0.35.0 canonical files     |     279 |     161,551,079 |
| Five generated global files |       5 |          15,954 |
| Proposed complete archive   | **803** | **469,993,991** |

The unchanged archive cap is **800,000,000 bytes**, leaving **330,006,009 bytes**. The independently derived metadata totals matched the completed local artifact exactly. Four hidden files are required: `.nojekyll` and each selected edition's original `site/.xonix-build.json`.

The exact v0.35 authority is source `9747b3e86e43d4e66b1c7b4aea6e05b220bf3ad5`, source TAR SHA256 `c5bdc9775b3cb5097cb42d83bc77030eeb36435f97ebea93172049ce00b959d8`, manifest SHA256 `57082613b02820815ac91bd18d5c31ad8309a7f78fd3e59f898c8c6f41a03496`, and ZIP SHA256 `3558ded7a8235b9ac708c71ec7fea169bb5d71f324014b8e4ccdbfa9b3bd3adb`. Its 275 manifest assets total 161,505,024 bytes. The 279 canonical rows include its unchanged release record, manifest, ownership marker and checksum sidecar. ZIP bodies stay on their original GitHub Releases; they are still verified during reproduction.

## Controller and preservation contract

The controller is exact frozen v0.37 source `c8abd4e4e48c34a9ae30255d2d4a2e9a74d593ed`, with Node **22.22.2**. All **44 release records / 45 tag objects** are locked, including the historical nonsemantic tag. All raw records, peeled commits and original tag objects must match before and after execution. A new tag requires a fresh reviewed binding; it is not silently admitted.

- Expected inventory SHA256: `e68d07aa5a80d27385d481204a8762d9195d3f7c0d1f03aee17262507ee14fc0`.
- Source lock SHA256: `6ca9a28c41ee7130675cdf04d86e29d4de2ed0c7771e3556208b83417b6b69c7`.
- Candidate allocation SHA256: `c7d60dbfac647d8a5d3a004dbdd21fa379801adb2301281110e6f66b9fc09df6`.
- Prior accepted Archive03 inventory: `dc1eb39fafeb5aab0dda962cf70917b04e5c6174d307988fbcc588222749f886`.
- Accepted local v0.37 main inventory supplying v0.35 rows: `433ab93ce2ef95ae3764ac621479c290562869b585e4d83f60ed3848e27c3f42`.

The allocation changes only Archive03's selected list from 033/034 to 033/034/035. Archive01/02 entries remain exact. This candidate contains an allocation input for the archive builder; it does not edit the game's main allocation. The archive index names latest hosted v0.35.0, while routing retains all 44 release records and describes 42 archived editions.

`tools/prepare.py` preserves the existing finite pipeline: validate exact source/record/tag/allocation/inventory authority and Node version; archive each selected tag; safely compare bounded ordinary TAR members against Git; run **each edition's own original CLI**; require exact manifest/ZIP hashes, ZIP member/CRC/body equality, loose inventory and accepted canonical rows; then assemble the archive with the pinned controller. All records are staged before `buildPages`, preventing its missing-record creation fallback. The builder cannot upgrade an old edition to current runtime behavior.

Local `--reuse-frozen-sites --frozen-root ...` remains available only as explicitly admitted verification of frozen outputs. It compares the retained TAR with a fresh Git stream, verifies its members, and retains all manifest/ZIP/body/hidden-file/post-run checks. It does not qualify a new archived CLI build. The hosted workflow defaults to three actual archived CLI builds. No check bypass, higher budget, schema change or player-data operation is introduced.

## Reproduction and remaining acceptance

The completed local run used `--reuse-frozen-sites`, exact retained c8 controller source and original releases. It verified all selected source TARs against fresh Git streams and bounded Git members, exact original manifest/ZIP/member/CRC/loose bytes, unchanged selected frozen trees, all 44 raw records and all 45 tag objects. The unchanged artifact verifier passed all 803 rows; HTTP `--check` passed with zero requests. Root independently reviewed the source and 63-file evidence packet before this feature PR.

Local handoff SHA256: `a71d6da464e509877ec2004cd22b50b14509e5293f43d1ad2ca4a8eb5ca41fab`. This is frozen reuse, not a fresh archived-CLI rebuild.

For a separately admitted reproduction, with Node 22.22.2 on PATH:

```sh
PYTHONDONTWRITEBYTECODE=1 /usr/bin/python3 archive/tools/test-verify.py
/usr/bin/python3 archive/tools/prepare.py --git-root source --builder-source source --out /absolute/new/archive03
/usr/bin/python3 archive/tools/verify-artifact.py /absolute/new/archive03/artifact
```

Use a fresh output directory and retain every failed attempt. A local reuse admission appends `--frozen-root /absolute/original/releases --reuse-frozen-sites`; a hosted run does not. Review the complete local receipt, selected frozen trees and all tag objects before any publication.

Then admit a reviewed feature PR against Archive03's actual current main, require the exact three-CLI hosted deployment and artifact checks, and audit **all 803 paths**, including four hidden files. The prepared HTTP helper retains bounded streaming, direct 200/no redirects, exact decoded bytes/SHA, finite transient-only retries, MIME and post-run preservation. It adds the existing main auditor's `application/octet-stream` rules for `.rlmedia` and `.rlstory` because v0.35 publishes Dawn example files. Do not run HTTP before exact deployment admission.

Root must separately qualify canonical v0.35 native launch, existing saved/earned owner restoration with the correct matching chapter, artwork, query/fragment continuity, offline preparation and any cold/disconnected claim. Initial missing-pack or missing-original observations remain evidence; archive copying does not repair or explain them. Preserve all edition storage keys, source owners, worker bytes and original release/tag objects.

Only after canonical acceptance may a later main milestone adopt the v0.35 allocation and qualify old-prefix retirement-worker forwarding. Keep the **950,000,000-byte main cap**, **12 installed packs**, **48 MiB index**, **256 MiB managed media**, and **64 MiB core cache** unchanged. No automatic eviction, cache erasure, forced worker takeover or silent migration is authorized by this preparation. Public v0.37 and future v0.38 delivery remain separate gates.
