# Strix security audit and hardening report

Audit date: 2026-10-31. Repository: https://github.com/usestrix/strix.git.
Upstream baseline: `6b7ae2ebe4d47037a927aade23265ff4e4f27e84`. Local branch: `security-hardening`.

**Release decision: code hardening completed, but NOT an unconditional launch clearance.**
Confirmed code findings below are fixed. Dependency re-audits are clear. Full-suite and type-check
failures already present upstream, Docker validation, and the compatibility checks listed below
remain release gates. No push, PR, deployment, paid scan, or live-target pentest was performed.
Only this isolated checkout was changed; no LULU production service or data was accessed.

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
