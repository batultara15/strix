# Pyright launch triage — 2026-11-01

Scope: saved 925-error project result, compared with the saved untouched upstream result.
No repository re-audit, checker relaxation, bulk code edit, or external validation was performed.

| Classification | Count | Evidence / disposition |
|---|---:|---|
| Confirmed launch-critical defects in these diagnostics | 0 | None reproduced as a launch defect during the focused runtime-contract review. This is not a proof that every diagnostic is harmless. |
| Pre-existing/non-launch-confirmed backlog | 925 | All normalized file/rule/message fingerprints are present in the untouched upstream result; none are new. Keep visible; not suppressed or waived. |
| Generated/vendor/test-only diagnostic locations | 0 | All 925 point into first-party `strix/` source. Third-party typing limitations can still cause first-party diagnostics. |

Breakdown: 838 unknown-type/boundary annotations; 31 runtime-contract candidates;
56 remaining static diagnostics (private access, cycles, unnecessary checks, unused/deprecated
annotations, and related checks). Counts cover all 925 saved errors.

The 31 contract candidates were reviewed in their exact source chunks: guarded stream closing,
trusted async child spawners, the stdio async-generator annotation, Jinja global inference,
validated reasoning values, guarded terminal selection, heterogeneous telemetry keyword dictionaries,
ReportLab's runtime canvas method, invariant dictionary annotations, Caido's validated literal sort
maps, completion-report interpolation, and dataclass/Pydantic serialization guards. No failing
production call was established from them. Pre-existing age alone was not used as a safety proof.
Unknown dynamic boundaries retain uncertainty and must be revisited if correlated with a failure.

The reproduced launch-relevant runtime defects were not flagged by these diagnostics. Windows path/descriptor timestamp
semantics falsely rejected unchanged source uploads. It was fixed by snapshotting descriptor
metadata consistently, retaining archive ctime, inode, device, size, mtime and regular-file guards.
The changed upload module passes targeted strict Pyright with zero errors and targeted Mypy.
Unchanged archive, changed-digest, replaced-path and same-inode rewrite regressions pass.
The final suite also exposed native drive colons incorrectly parsed as workspace destination
separators. That parser is fixed; its module retains exactly 82 baseline diagnostics and introduces
no new fingerprints. The workspace/subprocess-home affected tests pass 19 cases. The single full
run had 2,540 passes and three failures, subsequently fixed only with targeted tests; no full rerun
was performed, so a passing full result for the final code is still pending.

The project-wide strict Pyright gate is still not green. This triage is not an acceptance of that
backlog, a claim of complete runtime coverage, or permission to push/deploy. Private normalized
classification evidence is under `../strix-audit-evidence/pyright-*.json`; no raw logs or secrets
are committed. Docker, Intel Mac and CA retirement remain the previously recorded external gates.
