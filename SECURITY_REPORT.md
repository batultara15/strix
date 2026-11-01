# Strix security audit and hardening report

Audit date: 2026-10-31. Repository: https://github.com/usestrix/strix.git.
Upstream baseline: `6b7ae2ebe4d47037a927aade23265ff4e4f27e84`. Local branch: `security-hardening`.

**Release decision: code hardening completed, but NOT an unconditional launch clearance.**
Confirmed application-code findings below are fixed; local dependency re-audits and the latest
full-suite confirmation pass. The hardened Docker image has zero CRITICAL and zero actionable HIGH findings; two
source-only HIGH matches remain visible and are documented below. Type-check debt and Intel
compatibility/shared-CA retirement requirements remain. No push, PR, deployment, paid scan, or live-target pentest was performed.
Only this isolated checkout was changed; no LULU production service or data was accessed.

## Docker image dependency remediation — 2026-11-01

**Actionable image dependency gate: PASS. Raw Trivy: exit 1, with two retained source-only HIGH matches.**
Base revision remains `0c80e04d9bf7495c6f364ff152c8437d127d1544` on the isolated
`security-hardening` branch, with the Docker-only patch described here. No main LULU working
tree, application behavior, Sync v3, production credential, Cloudflare service, D1 or R2 was
accessed or modified. Nothing was pushed or deployed. Existing full local suite/audits were
not repeated. CCE was attempted first but its transport was closed; only the known Dockerfile,
reported package sources, image evidence and directly relevant tests were read.

The requested `docker-vulns.json` filename was absent. The actual verified before artifact is
`.venv/docker-validation-evidence/image-vulnerabilities.json`, SHA-256
`6a65b6f519b6a7d6e59557f02f1f1d4e685750a006a313877896c839ad1b0abf`.
Every one of its 118 findings was classified in ignored `hardening/classification-before.json`.
Counts are finding instances (not distinct CVEs):

| Root source | CRITICAL before / after | HIGH before / after | Disposition |
|---|---:|---:|---|
| Base image / OS packages | 0 / 0 reported | 0 / 0 reported | No base-image change warranted by this report; Kali coverage limitation below remains. |
| Go / bundled binary / runtime | 3 / 0 | 101 / 0 | Rebuilt affected tools with patched module versions and Go 1.27.3. |
| Python packages | 0 / 0 | 6 / 0 | Three installed Dirsearch cryptography matches fixed; three duplicate cache matches removed with unused cache. |
| Node packages | 0 / 0 | 4 / 0 | JSHint lodash/minimatch dependencies patched and locked. |
| Optional Rust source metadata | 0 / 0 | 4 / 2 | Two cache duplicates removed; two installed source-lock matches retained and proven non-runtime. |
| **Total raw matches** | **3 / 0** | **115 / 2** | **After: 0 actionable HIGH, 0 CRITICAL. No advisory ignored.** |

### Narrow fixes

- `containers/build-secure-tools.sh` rebuilds the same affected upstream tool releases with
  fixed dependencies: Gospider 1.1.6, httpx 1.12.0, interactsh 1.4.1, Katana 1.8.0, vulnx 1.0.0,
  Gitleaks 8.30.1 and Trivy 0.76.1. Gitleaks's old prebuilt Go 1.24.11 runtime is replaced.
  Key patched modules are `pgx/v5 5.9.0`, `compress 1.18.7`, `x/net 0.60.0`,
  `x/crypto 0.57.0`, `x/text 0.42.0`, `xmlquery 1.3.1`, `xpath 1.3.6`,
  `logrus 1.9.3`, and `go-jose/v4 4.1.6`. The crypto/text choices satisfy x/net's
  official module requirements. Existing compiler/module cache was reused for the build;
  only resulting binaries cross the existing multi-stage boundary. Builder caches are cleaned.
- `containers/install_dirsearch.py` verifies the exact official Dirsearch 0.5.0 source archive
  SHA-256 before safe extraction, then changes only its TLS requirements: pyOpenSSL 26.1.0
  to **26.4.0**, plus explicit **cryptography 50.0.2**. Upstream pyOpenSSL 26.1.0 requires
  cryptography below 48; simply upgrading cryptography fails dependency consistency.
  That draft was rejected by the retained `pip check`. The final source-built package passes
  `pip check`; scanner code and native source are unchanged. The download is a fixed public
  PyPI archive and extraction uses the safe `data` filter. An unexpected digest or source
  requirement fails closed. This local package requires rebuilding the image for updates;
  its temporary build source is removed, rather than promising `pipx upgrade` from that path.
- `containers/jshint/package.json` and its integrity-pinned lock retain JSHint **2.13.6**
  with compatible overrides **lodash 4.18.1** and **minimatch 3.1.5**. Installation uses
  `npm ci`; tests prove successful linting, syntax-error rejection and glob matching.
- `containers/Dockerfile` wires these package builds, drops old prebuilt Gitleaks/Trivy
  installers and removes unused uv/pip download caches. Installed tool functionality and
  entrypoint/CA code are retained. `containers/.gitattributes` enforces LF for shell scripts;
  `containers/__init__.py` makes the source-preparation helper importable by its tests.

### Remaining two HIGH matches: explicit applicability proof

Both are in
`home/pentester/.local/share/pipx/venvs/dirsearch/lib/python3.14/site-packages/dirsearch/native/Cargo.lock`:

| Advisory | Source dependency | Scanner fixed version | Current applicability |
|---|---|---|---|
| GHSA-36hh-v3qg-5ccf | pyo3 0.24.1 | 0.29.0 | Source only; no installed native extension. |
| GHSA-4w2j-m93h-cj5j | quinn-proto 0.11.14 | 0.11.15 | Source only; no installed native extension. |

The actual image regression proves `dirsearch_native` cannot be imported, no `.so` exists
anywhere in the installed Dirsearch package, its Python scanner help runs, and the updated
crypto/TLS runtime works. The normal source install does not compile Rust, consistent with
[upstream installation documentation](https://github.com/maurosoria/dirsearch/blob/master/docs/installation.md).
These are real advisories against optional source dependencies, not claims that the advisories
are false. Source files and findings remain present. Building/enabling that optional native
backend later requires fixing its source dependencies and validating that separate native build;
this release does not certify it. No `.trivyignore`, severity relaxation, vulnerability exclusion,
or new scan-directory exclusion was added. The raw scanner still exits **1** as required by
its unchanged threshold; the current Python-only runtime has **zero actionable HIGH** matches.

### Verification and immutable evidence

Final Docker build **exit 0** on Linux amd64, including the dependency-consistency, Brotli
and browser checks. New opt-in image tests in `tests/test_container_tool_security.py` verify
all seven compiled binaries' patched dependency metadata and offline CLI startup, JSHint
behavior, Dirsearch crypto/pyOpenSSL context creation and absence of native Rust binaries.
**All 13 unique new cases passed:** four source-patch unit cases and nine image cases.
An initial vulnx smoke test incorrectly used `-version`; its supported offline `--help`
probe passed after correcting only the test. The additional shared-library absence assertion
also passed. Targeted Ruff checks/formatting pass; no full local suite rerun was performed.

Unchanged real-container CA checks **PASS**: non-root execution, no generated key/P12 in
image, private file modes 0600, OS CA verification, matching NSS trust, distinct public CA
fingerprints in two containers, Caido HTTP 200, fresh CA and replaced trust after restart.
All checks used network-disabled containers without published ports, host mounts or Docker
socket mounts. Only public CA fingerprints were read; private keys/P12 were not exported.
All disposable image-test/CA/scan/SBOM containers were removed.

Final local tag: `strix-ca-check:hardened` (not published).

- Image index / Docker image ID: `sha256:473dd656256e1a8cbd560d3b9b27860db0f2260aa5146ce326cd7190e239677f`.
- Linux image manifest: `sha256:cb4d5d33dbc32341e9fb2e3f368121ab8918466b4e11c030a9f67bcd018f5abf`.
- Image config: `sha256:68a224e983b58701d9a6c001569575b31aebd51ab2350978255dd0f19b556cbb`.
- After scan JSON SHA-256: `631f0a92d1387986543c511cfd2ae3dc908eb15bcdd372846e2dde28bd4956fb`.

The same Trivy rootfs command/scope and HIGH/CRITICAL exit threshold were used before/after.
The final scanner is built from Trivy 0.76.1 source with patched go-jose; its CLI build-version
string is `dev`, not an official unmodified release executable. The scan inventory records
3,546 package entries; offline CycloneDX conversion produced 3,566 components. Kali is
identified as Debian `kali-rolling`, with a scanner OS-version/EOL mapping warning: zero
reported OS matches is not a blanket OS vulnerability clearance. This remains a merged-image
filesystem dependency scan, not an image-layer secret or image-configuration audit.

Ignored evidence is `.venv/docker-validation-evidence/hardening/`: `build-final.log`,
`source-hashes.json`, `classification-before.json`, `classification-after.json`,
`runtime-results.json`, `image-vulnerabilities.json`, `scan-summary.json`, `image-scan.log`,
`image-sbom.cdx.json`, `image-tests.log`, `vulnx-test.log`, and `dirsearch-test.log`.
The image's eight minimal build-context file hashes were rechecked after validation.

**External gates unchanged:** an actual Intel x86_64 macOS build/crypto/packaged-CLI runner
result is still missing. Shared-CA retirement still needs complete owned fleet/registry/trust
scope, old/replacement immutable image digests, public CA fingerprints and timestamped
retirement/no-old-trust evidence. No retirement or external validation is fabricated here.
This section supersedes the earlier image-dependency failure counts only; prior evidence is retained.

## Docker Desktop external validation — 2026-11-01

**Build/startup/CA checks: PASS. Image vulnerability gate: FAIL; launch remains blocked.**
Validated isolated branch `security-hardening` at exact source revision
`0c80e04d9bf7495c6f364ff152c8437d127d1544`; initially clean. Docker Desktop's Linux
engine is `29.9.2`, `amd64`, with four CPUs and approximately 4 GB RAM. Its per-user CLI
was not on PATH; using its installed binary/helper directory resolved the initial CLI error.
No implementation changes or previously passed local test reruns were performed.

Build used `containers/Dockerfile`, both referenced shell scripts, and
`strix/tools/proxy/caido_api.py` only, in a minimal context. Each copied file's SHA-256
matched the isolated source. No main LULU files, environment files, credentials, or private
keys entered the context. Build command: `docker build --platform linux/amd64 --progress plain
-f <minimal-context>/containers/Dockerfile -t strix-ca-check:0c80e04d <minimal-context>`;
exit **0**, including the Dockerfile's Brotli and browser-doctor checks. The image is local;
no registry push or deployment occurred. Immutable identities from build output:

- Image index / Docker image ID: `sha256:86be2f34d4a1b57c1f4a8973e99041b30e4a775ba2a230f265620426dc8b2008`.
- Linux image manifest: `sha256:0bae0c1c5376f4c45deea3fd705164d76cb6d4269bc98490b6de8cf65a55448b`.
- Image config: `sha256:385699de3aad495e7432c3fcd82e21e58f0bb63c3f04fa9958f505d097cf9cf8`.

The finished image contains neither `/app/certs/ca.key` nor `/app/certs/ca.p12`.
Two disposable containers ran the unmodified entrypoint with `--network none`, no host
mounts or published ports. Both reached readiness and Caido HTTP **200**, ran non-root,
and had private key/P12 modes **0600**. Each public CA verified against the OS bundle and
matched its NSS `Testing Root CA` entry; the two containers' fingerprints differed.
Restart generated a third, different fingerprint and updated both OS and NSS trust correctly.
Only public fingerprints and file modes were inspected; no private key/P12 material was
printed or exported. An early probe timed out during image unpacking, before startup;
the complete post-unpack runtime run passed. All disposable audit containers were removed.

Image scan used bundled **Trivy 0.76.1** in a disposable container, overriding the entrypoint:
`trivy rootfs --scanners vuln --skip-dirs /proc,/sys,/dev,/tmp --list-all-pkgs
--severity HIGH,CRITICAL --exit-code 1 --format json /`.
This scans the built image's merged filesystem, without a Docker socket or host mount;
it is not an image-layer secret/history or configuration scan. Scan exit **1**:
**118 finding instances: 115 HIGH and 3 CRITICAL, across 70 unique vulnerability IDs**.
Instances include repeated installed/cache/source-lock locations; exploitability and duplicate
triage remain outstanding. CRITICAL package matches:

| Image binary | Advisory | Installed dependency | Scanner fixed version |
|---|---|---|---|
| `home/pentester/go/bin/katana` | CVE-2026-33815 | `github.com/jackc/pgx/v5 v5.7.2` | 5.9.0 |
| `home/pentester/go/bin/katana` | CVE-2026-33816 | `github.com/jackc/pgx/v5 v5.7.2` | 5.9.0 |
| `usr/local/bin/gitleaks` | CVE-2025-68121 | Go stdlib v1.24.11 | 1.24.13 / 1.25.7 / 1.26.0-rc.3 |

Other matches include bundled cryptography 47.0.0, lodash, minimatch and upstream Go/Rust
binaries. These image-tool dependencies are separate from the already passing host-project
lockfile audits. Do not distribute this image until findings are remediated or explicitly
reviewed/dispositioned. Trivy identified Debian `kali-rolling` and warned that this OS version
is not on its EOL list; zero reported OS matches does not establish complete Kali coverage.
The JSON contains 3,840 package entries; offline conversion produced a CycloneDX SBOM with
3,861 components (different counting includes dependency components).

Private local evidence is retained only under ignored `.venv/docker-validation-evidence/`:
`build.log`, `runtime-results.json`, `image-vulnerabilities.json`, `image-scan.log`,
`scan-summary.json`, and `image-sbom.cdx.json`, plus minimal context/probe scripts.
Vulnerability JSON SHA-256:
`6a65b6f519b6a7d6e59557f02f1f1d4e685750a006a313877896c839ad1b0abf`.
This section supersedes historical statements that Docker was unavailable; it does not
supersede Intel or retirement gates. Intel validation still requires an actual **x86_64
macOS runner** building this revision and passing native crypto/packaged-CLI smoke checks.
Shared-CA retirement still requires the complete owned deployment/registry/trust-store
scope, old and replacement immutable image digests, public CA fingerprints, and timestamped
proof that no old image/container or old trusted CA remains in that scope. None was supplied.
No main LULU working-tree change, Cloudflare access, production credential access, D1/R2
operation, live-service operation, push or deployment occurred. Only this report is changed.

## Full-suite confirmation — 2026-11-01

One full Python test-suite run after the latest fixes completed successfully:
**2,543 passed, 15 skipped, 3 xfailed, zero failures/errors**, with 122 warnings, in 621.97 seconds.
JUnit records 2,561 total test cases, including 18 skipped/expected-failure cases.
The three failures from the previous run are resolved. No implementation change or second run
was required during this confirmation task. Private evidence: `confirmation-suite.log` and
`confirmation-suite.xml` in `../strix-audit-evidence/`.

Local test validation: **PASS**. This supersedes earlier statements that final full-suite
confirmation was pending; the historical results below remain preserved. Skips and xfails are
not claimed as executed passing coverage. Existing external gates and the retained Pyright
baseline were not changed, retried, or reclassified. No push, deployment, production/D1/R2 write,
or LULU/Sync v3 modification occurred. This confirmation updates only this report.

## Local launch follow-up — 2026-11-01

The saved full-run failure indices were mapped by collection only, then failing groups were
reproduced with bounded targeted commands. The real upload failure was a Windows `lstat`/`fstat`
ctime mismatch: path metadata could report creation time while descriptor metadata reported
change time. Selection now snapshots validated descriptor metadata, using the same API as archive
validation. No archive integrity guard was removed. Four focused unchanged/mutation/digest tests
pass; the affected upload suite passes 30 tests with two capability skips.

Other reproduced failures were stale test fixtures: missing skill/telemetry settings, the previous
Go minimum in a packaging assertion, hardcoded `/usr/bin/env`, a POSIX-only mount target, illegal
Windows display-name fixtures, overlong pytest IDs, and POSIX mode-bit assertions. Private-file tests
now verify actual 0600 creation requests on every platform, and actual mode bits on POSIX. Real
symlink tests skip only on Windows error 1314; other errors still fail. This does not claim Windows
ACL validation or replace required capable-runner checks.

Existing targeted results: budget/packaging 5 passed; runner paths 12 passed; threat-model,
argument and native-root fixtures 58 passed; portable contract cases 3 passed/2 capability skips;
viewer/identity permission cases 2 passed. No passed dependency/security/frontend audit was repeated.
See [PYRIGHT_LAUNCH_TRIAGE.md](PYRIGHT_LAUNCH_TRIAGE.md) for classification of all 925 saved errors:
zero confirmed launch-critical type defects, 925 retained baseline diagnostics, zero vendor/test-only
locations. The changed production upload module passes targeted Pyright and Mypy.

A single final full-suite run was started only after no recorded local failure remained unresolved,
with a private external pytest-timeout plugin (90 seconds per test). Result: **2,540 passed,
15 skipped, 3 xfailed, 3 failed**, in 714.56 seconds. The three new failures were then fixed:
two exposed a real Windows drive-colon bug in `PATH[:DEST]` parsing; the third was a child-process
fixture that removed Windows home variables. Both source/destination parsing now share a native
drive-aware split, retaining destination traversal/control-character validation. The child uses an
isolated temporary home on both platforms. Their two affected modules pass **19 tests** after fixes.
Targeted Mypy passes; the parser module retains exactly its 82 baseline Pyright fingerprints, with
zero new diagnostics. No second full-suite run was performed: full-suite confirmation of the final
code remains pending, despite all reproduced failures passing targeted checks.

Docker/Intel/shared-CA blockers were recorded from existing evidence only; no retry, push,
deployment, production/D1/R2 write, or LULU/Sync v3 change occurred. Strict Pyright's 925-error
baseline is retained and unwaived. This work is not production-launch clearance.

## First remaining full-suite failure (2026-11-01)

The original progress log's first `F` is test index 431. Collection-only mapping identified
`tests/test_cloud_cli_runtime.py::test_source_prompt_shows_paths_and_literal_confirmation`;
only that case was rerun to reproduce the failure. It raised Windows `OSError: [Errno 22]`
while creating a filename containing ESC/BEL control bytes, before the application ran.

The prompt fixture now creates ordinary temporary files and injects the same hostile display
name into the prepared manifest. All original escaping/literal-confirmation assertions remain,
and cancellation must remove the real temporary archive. No production implementation changed.
The complete affected Cloud CLI runtime test file passes: **75 passed**. No full-suite rerun
or repeat of dependency, vulnerability, frontend or secret scans was performed.

Targeted strict Pyright on `cloud/source_scan.py`, `cloud/source_upload.py`, `cloud/render.py`
and `terminal_text.py`: **zero errors**. These affected modules had no recorded errors before
this fix either. The last project-wide backlog remains **925**, unresolved; unrelated files
and type-checker settings were not edited. Changed-test Ruff/format and `git diff --check` pass.

External blockers were taken from the existing report/configuration, without repeated probes:
Docker/usable Linux runtime unavailable; Intel macOS hardware/runner validation unavailable;
shared-CA retirement requires the owned deployed-image/container digests and old CA trust
fingerprint inventory. No retirement, push, deployment or production/D1/R2 operation occurred.
LULU and Sync v3 remain untouched. Other full-suite failures remain unverified.

## Launch-blocker follow-up (2026-10-31 to 2026-11-01)

This follow-up changes only this isolated Strix checkout. It does not repeat the audit,
push/deploy, access production, or change LULU/Sync v3/D1/R2. Launch clearance is still withheld.

| Blocker | Follow-up result |
|---|---|
| Baseline tests | Required `skills=[]` restored in the budget test fixture; adversarial pytest IDs are named without shortening their payloads. 147 targeted tests pass across baseline/platform/auth (100), native crypto (2), pricing (44), and the formerly stalled provider case (1). The single full-suite attempt reached 75% with additional failures/errors, then spent hours in interactive provider authentication from cost estimation. It was stopped; no second full run was started. Full-suite launch clearance remains unresolved. |
| Mypy | All six platform-related errors fixed with explicit optional POSIX Protocol contracts, retaining existing lock/fallback and Linux-only UID behavior. Final check: no issues in 136 source files. |
| Strict Pyright | Touched auth/platform modules pass with no errors. Validated JSON boundary/generator annotations remove 16 baseline diagnostics: project total 941 -> 925. The remaining strict-typing backlog is unresolved; no exclusions, ignore rules, relaxed settings or baseline acceptance were added. |
| Cost-estimation hang | Proven from the running test stack: the local pricing resolver selected a GitHub Copilot entry; LiteLLM inferred its provider and entered device-login polling from `completion_cost`. Both local-estimation calls now pass the resolved provider explicitly. Two regressions forbid provider discovery; the previously stalled fake-gateway case passes in 1.42 seconds with the pricing callback installed. No authentication setting was relaxed. The changing external pricing-map assertion now uses controlled fixture data. |
| Intel macOS | Official cryptography 50.0.2 artifact metadata has no Intel macOS wheel. Existing Intel release job now prepares Rust/OpenSSL and static linking, then runs native crypto and packaged CLI smoke tests. YAML/order checks, pinned actionlint and both crypto tests pass locally on Windows. No Intel runner execution occurred: compatibility remains unverified. |
| Docker | No Docker executable/service or usable Linux/WSL runtime is available. No image was built, started, scanned or published. CA startup, trust-store and two-container isolation checks remain unverified. |
| Old shared-CA retirement | No deployed-image/container inventory, registry ownership scope or old CA fingerprint list is available in this public source checkout. No image, container, registry tag or trust entry was deleted. Retirement is NOT confirmed. |

Intel build preparation follows the [cryptography source-build instructions](https://cryptography.io/en/latest/installation/#building-cryptography-on-macos);
wheel availability was checked using [official release artifact metadata](https://pypi.org/pypi/cryptography/50.0.2/json).
A prepared CI step is not evidence of an executed Intel build.

To close the infrastructure gates, use an isolated Linux Docker host and an actual Intel Mac runner
on this branch. Obtain the owned deployed-image/container inventory (immutable digests) and the
old CA fingerprints, replace affected instances only after a validated new build, remove their trust
entries wherever imported, and verify no affected instance/digest remains active. Source remediation
cannot retire somebody else's distributed image or erase an already-disclosed private key.
Do not delete unknown images or trust material, and do not deploy as part of this follow-up.

Changed-file Ruff/format, pricing Bandit, actionlint, and `git diff --check` pass.
The only whole pytest run was terminated after diagnosis; its partial output is not a passing result.
The stopped audit test process is no longer running.

Follow-up fix commits: `ba16da6b`, `109d4f59`, `8528356f`, `f2857cb1`, `a6e5dc9a`, `e890eaae`.

Evidence remains private in `../strix-audit-evidence/launch-*.log`. The earlier audit/test records
below are historical results, not claims that these outstanding gates are cleared.

## Reconnaissance and architecture (10 lines)

1. Python 3.12+ CLI enters at `strix.interface.main:main`; Pydantic settings consume env/JSON configuration.
2. `interface/scan_setup.py` accepts paths, URLs, repository targets, API specs, instructions and resume state.
3. OpenAI Agents SDK/LiteLLM route operator-approved scan context to external model providers.
4. `core/` and `agents/` orchestrate sessions, tool calls, budgets and agent lifecycle on the host.
5. `runtime/` creates Docker sandboxes and selected source mounts; sandbox commands intentionally execute code.
6. Go/Bubble Tea in `interface/tui/` is a local sidecar using a host-controlled protocol connection.
7. The stdlib HTTP viewer serves local run artifacts through a per-process capability/session boundary.
8. React 19/TypeScript/Vite/Tailwind render reports, markdown and escaped highlight.js output.
9. Cloud clients call `/api/v1`, pin stored credentials to their issuer, and gate source uploads by digest approval.
10. Kali Docker builds, GitHub Actions, uv.lock, npm package-lock and Go modules form the supply-chain boundary.

### Scope map

| Area | Entry points / inputs | Trust boundary reviewed |
|---|---|---|
| CLI/config/auth | `interface/main.py`, `cli_args.py`, `auth_cli.py`, `config/codex.py` | Operator inputs, OAuth state, secret persistence |
| Cloud integration | `interface/cloud/`, `platform_cli.py` | Bearer origin binding, redirects, upload selection, payment proxy |
| Local HTTP | `interface/viewer/server.py` | Network callers versus capability-authorized run data and steering |
| Reports/UI | `report/`, `viewer/frontend/src/` | Model/target-controlled content versus filesystem/HTML/CSV output |
| Sandbox/tools | `runtime/`, `tools/`, `containers/` | Host filesystem/credentials versus intentionally executable sandbox work |
| Build/release | `.github/`, `scripts/`, Dockerfile, lockfiles | Dependency integrity, workflow permissions, artifacts and executable installers |

The audit combined manual call-chain review with whole-source Bandit/Ruff checks, dependency
advisory scans, and redacted Gitleaks history/tree scans. This is not a claim that every possible
execution path was dynamically exercised. The hosted Strix backend and deployed container images
are not contained in this checkout and were not black-box tested.

## Findings table (presented before remediation)

No Critical issue was confirmed. Severity reflects the relevant attack prerequisites; package-audit
severity is distinguished from a demonstrated reachable production exploit.

| ID | Severity | File:line (hardened tree) | Issue / impact | Fix plan and result |
|---|---|---|---|---|
| SEC-01 | High | `strix/interface/utils.py:1255,1553` | `..` survives name sanitization; clone removed a predictable target-derived destination before invoking Git. Crafted input could delete host files outside the intended run directory. | **Fixed:** reject special/unsafe components, unique private directories, no pre-clone recursive deletion, Git option terminator. |
| SEC-02 | Medium | `strix/interface/viewer/server.py:159,222` | Unbounded/negative request lengths and unlimited socket wait enable resource exhaustion, including unauthenticated telemetry requests on an exposed viewer. | **Fixed:** 64 KiB body cap, reject malformed/duplicate lengths and transfer encodings, 10-second connection timeout. |
| SEC-03 | Low | `strix/interface/viewer/server.py:163,167` | Debug access logs included bootstrap capability query strings; sensitive viewer responses lacked cache/referrer protections. | **Fixed:** omit access-log queries; no-store, no-referrer, nosniff and frame denial headers. |
| SEC-04 | High (scanner-rated; frontend toolchain) | `strix/interface/viewer/frontend/package-lock.json:1785` | Six affected frontend packages; build/dev-tool DoS and dev-server file disclosure advisories. No claim that all are reachable in the shipped static viewer. | **Fixed:** independent Browserslist chain, nanoid, source-map-js, PostCSS and Vite updates with lock guards and rebuilds. Final npm audit: zero. |
| SEC-05 | High (mixed package advisories) | `pyproject.toml:53,81`, `uv.lock` | Twelve affected locked Python packages, including parsers, HTTP/auth and cryptography dependencies. Initial audit reported 121 entries, including duplicates, not 121 distinct proven exploits. | **Fixed:** per-package commits, patched constraints/locks, installed-version guards and existing consumer tests. Final pip-audit: zero. |
| SEC-06 | High on shared hosts | `strix/interface/utils.py:1504,1516` | Predictable API-spec temp directories allow local pre-placement/write interference and potential disclosure of credential-bearing specs. | **Fixed:** unique private staging directories for fetched and copied specs; old-path preservation and traversal tests. |
| SEC-07 | High | `containers/Dockerfile:263`, `containers/generate-ca.sh:1` | Interception CA signing keys were generated in an image layer and shared by all users of that image, enabling impersonation of TLS endpoints trusted by those containers. | **Fixed in source:** fresh per-container key/certificate generation before Caido; restrictive key modes; runtime trust-store installation. Rebuild/retire old images and trust material before launch. |
| SEC-08 | Low in analyzed build | `strix/interface/tui/go.mod:14,31` | Affected x/sys and x/text modules; initial Windows scan found dependency/package matches without reachable vulnerable-symbol traces. | **Fixed:** x/sys v0.44.0, x/text v0.41.0; Go tests/vet and final symbol scan pass. |
| SEC-09 | Medium | `strix/interface/update_check.py:323` | Executable self-update continued without published checksum metadata. | **Fixed:** require a valid SHA-256 digest before download, reject mismatches before extraction/replacement; missing/invalid/mismatch/success regressions pass. |
| SEC-10 | Medium | `strix/interface/utils.py:1553` | Repository URLs with inline HTTP credentials and raw Git failure diagnostics could disclose credentials in terminal/log output. | **Fixed:** reject URL credentials/query/fragment before logging or Git execution, retain SSH username support, and emit only a generic failure exit code. Fake-secret regressions assert no disclosure. |

## Dependency remediation detail

Each Python package has its own fix commit. The regression test checks both locked and installed
versions; consumer suites were run after each update. Links below are representative advisories;
complete raw scanner records remain in local redacted audit evidence.

| Python package | Before | After | Representative advisory |
|---|---|---|---|
| anyio | 4.14.1 | 4.14.2 | [PYSEC-2026-4025](https://osv.dev/vulnerability/PYSEC-2026-4025) |
| certifi | 2026.6.17 | 2026.10.23 | [PYSEC-2026-4320](https://osv.dev/vulnerability/PYSEC-2026-4320) |
| cryptography | 48.0.1 | 50.0.2 | [PYSEC-2026-3554](https://osv.dev/vulnerability/PYSEC-2026-3554) |
| filelock | 3.29.4 | 4.2.1 | [CVE-2026-112940](https://osv.dev/vulnerability/CVE-2026-112940) |
| litellm | 1.101.0 | 1.101.3 | [CVE-2026-114612](https://osv.dev/vulnerability/CVE-2026-114612) |
| mcp | 1.28.1 | 1.30.0 | [CVE-2026-59951](https://osv.dev/vulnerability/CVE-2026-59951) |
| multidict | 6.7.1 | 6.9.1 | [PYSEC-2026-4244](https://osv.dev/vulnerability/PYSEC-2026-4244) |
| pillow | 12.3.0 | 13.0.0 | [PYSEC-2026-4327](https://osv.dev/vulnerability/PYSEC-2026-4327) |
| pyasn1 | 0.6.4 | 0.6.5 | [CVE-2026-119196](https://osv.dev/vulnerability/CVE-2026-119196) |
| pyjwt | 2.13.0 | 2.15.0 | [PYSEC-2026-4145](https://osv.dev/vulnerability/PYSEC-2026-4145) |
| pypdf | 6.14.2 | 6.21.4 | [PYSEC-2026-3656](https://osv.dev/vulnerability/PYSEC-2026-3656) |
| urllib3 | 2.7.0 | 2.8.0 | [PYSEC-2026-4177](https://osv.dev/vulnerability/PYSEC-2026-4177) |

Frontend changes: browserslist 4.28.6 -> 4.29.5; baseline-browser-mapping 2.10.43 -> 2.11.33; nanoid 3.3.16 -> 3.3.20; source-map-js 1.2.1 -> 1.2.2; postcss 8.5.19 -> 8.5.31; vite 6.4.4 -> 6.4.5. The npm lockfile audit is authoritative.
Advisories include [Vite GHSA-8g5g-mxqh-grgj](https://github.com/advisories/GHSA-8g5g-mxqh-grgj)
and [Browserslist GHSA-c83g-rgw3-j3cx](https://github.com/advisories/GHSA-c83g-rgw3-j3cx).

### Compatibility / behavior changes that require attention

- Viewer bodies larger than 64 KiB, malformed/duplicate Content-Length, or unsupported Transfer-Encoding
  are now rejected. This is intentional security behavior; normal steering/feedback payloads fit below the cap.
- Clone/spec temporary paths are unique rather than reusable/predictable. The helpers still return the actual path.
- Repository URLs with inline HTTP credentials, passwords, queries or fragments are rejected before logging/execution. Use SSH or a Git credential helper; SSH usernames remain supported.
- Go dependency fixes raise the source module minimum from Go 1.24 to 1.25; release builds now select Go 1.27.x.
- cryptography changes from `>=48.0.1,<49` to `>=50.0.2,<51`. The old cap explicitly protected Intel macOS
  wheel availability. Intel macOS source/wheel builds must pass with the required Rust/OpenSSL toolchain;
  do not publish an untested Intel artifact. No public CLI/API rename was made. Self-update now intentionally refuses releases without verifiable checksum metadata; use a verified package-manager/manual upgrade instead.
- pyasn1 0.6.5 and pypdf 6.21.4 were too recent for the global five-day cooldown. They are exactly pinned,
  hash-locked, reviewed security-fix exceptions with a bounded 2026-10-31 cutoff. The global cooldown
  remains enabled for other packages. Revisit/remove those exceptions once mature; never exempt arbitrary latest releases.

## Secrets review and required rotation

Gitleaks was downloaded from its official release and checksum-verified. Scans used `--redact`;
no candidate credential values were printed or added to this report. History scans found nine
candidates: one synthetic AWS log-redaction fixture, five documentation/prose/example occurrences,
and three historical occurrences of the explicitly public PostHog ingestion project key.
No privileged production credential was confirmed. These findings are retained and triaged, not
hidden behind a blanket allowlist. Public telemetry ingestion identifiers are not personal/read API keys.
The current source tree had two matching documentation/public-ingestion candidates.

**Mandatory rotation/replacement:** retire previously distributed sandbox images/containers and their
shared interception CA trust material. The source fix creates fresh instance keys; it cannot revoke
keys already obtained from old images. Do not export the sandbox CA into a host-wide production trust store.
If an owner independently identifies any historical candidate as a real privileged credential, revoke it,
replace it through the existing environment/secret-file configuration, and coordinate history cleanup;
this audit deliberately did not rewrite upstream history or push credentials anywhere.

## Coverage of requested audit classes

| Class | Result / practical boundary |
|---|---|
| Secrets and history | Redacted full-history/tree scan; classified candidates; image CA issue fixed. |
| SQL/NoSQL/deserialization/eval | No new host-side exploitable SQL/NoSQL or unsafe deserialization/eval sink confirmed; SDK/local storage and structured serialization reviewed. Scanner/example payloads are not application execution. |
| Shell/path injection | Host clone deletion/staging boundaries fixed; subprocess argument lists reviewed. Sandbox shell execution is an intentional product capability, not a host RCE finding by itself. |
| SSRF | Cloud URL/origin and no-redirect controls reviewed; network probing of operator-selected targets, including localhost, is intentional. Do not expose this CLI as an untrusted multi-tenant service. |
| Auth/session/IDOR | Local viewer capability checks, history gate, OAuth callbacks, credential issuer pinning, strict cookies and secret-file atomic writes reviewed. Hosted server authorization is outside this repository. |
| XSS/CSRF/CORS/redirects | React-markdown/highlighter output paths reviewed; arbitrary raw report HTML is not directly enabled. Viewer uses capability cookies/SameSite; no permissive CORS added; cache/referrer/frame protections improved. HSTS is not appropriate for the default plain-HTTP loopback endpoint. |
| Validation/errors/logs | Body/framing limits, bootstrap-log redaction and Git credential/diagnostic disclosure fixed; source-upload bounds and identity/symlink guards reviewed. |
| Files/temp/uploads | Clone/spec temp issues fixed; archive selection/read guards and generated report IDs reviewed. |
| Crypto | Shared image CA key issue fixed; crypto dependencies patched; generated credentials use secure randomness. |
| CI/build/container | Action references are SHA-pinned, workflow defaults are read-only and checkout credentials are not persisted. Release write permission is job-scoped. Go toolchain hardened; full container build/image scanning remains a manual release gate. |
| Prompt injection | Treat target/model text as untrusted. Prompts do not replace sandboxing. Writable source mounts, host gateways, MCP servers and operator-enabled privileges remain powerful intentional capabilities requiring deployment isolation. |

## Verification results

| Check | Result |
|---|---|
| New + existing affected Python suites | 294 passed, 1 POSIX-only CA test skipped, 1 known Windows mode-bit test deselected. |
| Per-fix Python consumers | Passed for each package update, including 106 LiteLLM consumers/guards and PDF/MCP/model suites. |
| Frontend dependency regressions | Six lockfile-version guards passed; rebuilt after every independent frontend fix. |
| Ruff lint + formatting | Passed. |
| Bandit | Project-configured check passed with zero findings. An additional default-policy scan reports 30 Low alerts (assert/subprocess rules excluded by the existing project policy); reviewed as intentional guarded uses, not silently claimed absent. This does not replace manual review. |
| npm audit | Six findings before -> zero after. |
| pip-audit frozen production inventory | Twelve affected packages before -> zero known advisories after. |
| Go tests / vet | All TUI packages passed on Windows/amd64 with Go 1.27.3. |
| govulncheck | Final Windows and Linux source/symbol scans: zero findings. |
| Executable updater | 36 existing/new tests passed, including missing/malformed digest refusal, mismatch preservation and valid archive replacement. |
| Shell / CA smoke | Git Bash syntax checks passed; two OpenSSL generations produced distinct certificates and valid PKCS12 files without logging keys. |
| uv lock --check / git diff --check | Passed. |
| Full pytest suite | Not green. Native run hit Windows's 32,767-character environment limit for adversarial parameter IDs. External runner hashed display IDs only: 158 passed, then stopped after five stale budget-policy test failures (`_start_child_runner` missing required `skills`). No adversarial input was shortened. |
| mypy | Six errors in two unchanged POSIX-dependent files (`config/codex.py`, `runtime/session_manager.py`). Requires Linux validation / platform-typing cleanup. |
| Pyright | Strict project check is not green: both untouched baseline and hardened source report exactly 941 errors with the same interpreter. Do not interpret a bare wrong-interpreter run's missing-import cascade as a code-fix regression. |
| Docker build / image scan / live deployed behavior | Not executed: no Docker daemon available. Source tests do not establish image startup or an image's CVE state. |
| Secret re-scan | Redacted history scan retained nine triaged candidates; not presented as a zero-alert scan. |

The stale budget-policy test call sites and their production function signature are unchanged from
upstream. These failures must be resolved or explicitly dispositioned by maintainers before release;
they are not a reason to silently skip tests or claim all checks passed.

## Remaining / unaccepted launch risks and manual actions

1. Rebuild the Docker image and validate Caido startup, generated CA permissions, OS trust store and browser trust.
   Confirm two real containers have different CA fingerprints. Retire old distributed CA-bearing images.
2. Run the full Linux test/type-check suite and repair/disposition baseline failures. Run the supported
   Python-version matrix and Intel macOS packaging job. No production-ready certification is made here.
3. Docker builds intentionally still include rolling Kali packages and upstream tool installers/latest versions.
   These are supply-chain/reproducibility risks, not cleared by the Python/npm/Go audits. Before distributing
   a production image, review/pin its resolved tool inventory, generate an SBOM, scan the built image with
   Trivy (or equivalent), and deploy by immutable image digest. A compromised upstream installer remains a risk.
4. Container sudo and NET_ADMIN/NET_RAW, optional SYS_ADMIN/FUSE, host gateways and writable source mounts
   are intentional pentest capabilities. Use dedicated disposable hosts, restrict mounts/egress, avoid Docker
   socket exposure, and never treat this as a hardened untrusted-tenant execution service.
5. Local HTTP viewer sessions are capabilities. Keep loopback binding by default; use a trusted authenticated
   TLS gateway for remote access. Avoid untrusted services sharing the loopback hostname/cookie scope.
6. Self-update now fails closed without a published SHA-256 digest. Installers/build
   tool chains still need an independently signed, immutable provenance policy for high-assurance releases;
   no claim is made that GitHub HTTPS plus same-origin checksums withstand upstream-account compromise.
7. Owner actions: enable repository secret scanning/push protection and branch protection; require security
   dependency scans and the full build/test matrix before merging. No GitHub organization settings were changed.

## Pre-launch checklist

- [x] Review and commit fixes on `security-hardening`, never main.
- [x] Add regressions for every confirmed code issue and advisory-affected dependency group.
- [x] Re-run Python/npm/Go advisory scans and redacted secret scanning.
- [x] Preserve CLI behavior except the documented security/compatibility changes.
- [ ] Full Linux/Python matrix green; stale budget test calls and type-check errors resolved/dispositioned.
- [ ] Intel macOS build validated after cryptography cap change; Go source-build requirement communicated.
- [ ] Rebuilt Docker image tested, SBOM/image scan reviewed, immutable digest selected.
- [ ] Old shared interception CA images/trust retired; only per-instance CA keys used.
- [ ] Remaining rolling installer/update/provenance risks explicitly reviewed and accepted or remediated.
- [ ] Secrets and runtime credentials provisioned through env/private files; no real credentials in artifacts.
- [ ] Maintainer reviews this branch and requires passing CI before merge/deployment.

## Separate remediation commits

```text
950c837e fix(security): confine repository clones to private temporary directories
c8259f23 fix(security): bound viewer request bodies and socket lifetimes
52fe3f37 fix(security): prevent viewer capabilities leaking through logs and caches
9c4636c0 fix(deps): patch Browserslist and baseline mapping advisories
e5fa33b4 fix(deps): patch nanoid security advisories
1176200a fix(deps): patch source-map-js security advisories
cf1aa907 fix(deps): patch postcss security advisories
d3c1fa3d fix(deps): patch vite security advisories
cab8e803 fix(deps): require patched LiteLLM release
cdd41b13 fix(security): stage API specifications in private unique directories
6880973b fix(deps): require patched anyio release
6a53418e fix(deps): require patched certifi release
3d550e88 fix(security): generate interception CA keys per container instead of per image
894161b0 fix(deps): require patched urllib3 release
8482fd86 fix(deps): require patched pyjwt release
47ffe3d8 fix(deps): require patched mcp release
902da9fd fix(deps): require patched multidict release
fd585b37 fix(deps): patch Go syscall dependency and require Go 1.25
a99eab72 fix(deps): require patched filelock release
9dad3f8b fix(deps): require patched pyasn1 release
73120324 fix(deps): patch Go text advisories and validate builds on supported Go
a576896f fix(deps): require patched pypdf release
0a613884 fix(deps): require patched pillow release
35f43e4f fix(deps): require patched cryptography release
0a60599f fix(security): refresh browser trust after per-container CA rotation
749af956 fix(security): refuse executable updates without a verified checksum
b1c113b4 fix(security): keep repository URL credentials and Git diagnostics out of logs
```

## Reproduction commands

Run from the isolated repository using the installed frozen environment. On Linux, use
`.venv/bin/python` in place of the Windows Python path below. Build output must stay outside source.

```text
uv sync --frozen --no-install-project
.venv/Scripts/python.exe -m pytest -q tests/test_clone_security.py tests/test_api_spec_targets.py tests/test_viewer_security.py tests/test_viewer_runs_gating.py tests/test_viewer_auth.py tests/test_viewer.py tests/test_dependency_security.py tests/test_go_dependency_security.py tests/test_container_ca_security.py tests/test_models.py tests/test_mcp_client.py tests/test_report_pdf.py tests/test_update_check.py -k "not test_write_auth_is_0600"
.venv/Scripts/python.exe -m ruff check strix tests
.venv/Scripts/python.exe -m ruff format --check strix tests
.venv/Scripts/python.exe -m bandit -r strix -c pyproject.toml
node --test tests/frontend_dependency_security.test.cjs
npm ci --ignore-scripts --prefix strix/interface/viewer/frontend
npm audit --prefix strix/interface/viewer/frontend
npm run build --prefix strix/interface/viewer/frontend -- --outDir <absolute-external-build-directory>
uv export --frozen --no-dev --no-emit-project --format requirements-txt --output-file <external-requirements-file>
uvx pip-audit --disable-pip --no-deps -r <external-requirements-file>
uv lock --check
git diff --check
```

In `strix/interface/tui`, run `go test ./...`, `go vet ./...` and `govulncheck ./...`.
Run `gitleaks git --redact` for history and `gitleaks dir --redact` on a source-only snapshot;
retain/redact scanner output privately. Re-enable the POSIX mode-bit test and execute the
Linux CA runtime test on Linux. The full launch gate remains `make check-all` plus the full
pytest suite and supported build matrix, not only the selected passing suites above.

## Local evidence

Tool output, redacted scanner JSON, dependency snapshots and build/test logs are in the ignored sibling
`../strix-audit-evidence/` directory. Generated CA test keys remain there only, never in this branch.
No evidence file containing candidate values, tokens, credentials or customer data is committed.
The authoritative artifacts for reproducing scans are the committed lockfiles and the commands above;
raw local logs should be reviewed/redacted before sharing externally.
