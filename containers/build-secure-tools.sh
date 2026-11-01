#!/bin/sh
set -eu

# Rebuild the same releases; upstream executables can embed old Go runtimes.
go_version="$(go env GOVERSION)"
minimum="$(printf '1.27.3\n%s\n' "${go_version#go}" | sort -V | head -n 1)"
[ "$minimum" = 1.27.3 ] || {
    echo 'Patched Go toolchain 1.27.3 or newer required' >&2; exit 1;
}

build_tool() (
    module="$1" version="$2" command="$3" output="$4"
    shift 4
    go mod download "$module@$version"
    work="$(mktemp -d)"
    trap 'rm -rf "$work"' EXIT
    cp -a "$(go env GOPATH)/pkg/mod/$module@$version/." "$work/"
    chmod -R u+w "$work"
    cd "$work"
    go get "$@"
    go mod tidy
    go build -p 2 -trimpath -o "/out/bin/$output" "$command"
    go version -m "/out/bin/$output"
)

build_tool github.com/jaeles-project/gospider v1.1.6 . gospider \
    github.com/antchfx/xmlquery@v1.3.1 github.com/antchfx/xpath@v1.3.6 \
    github.com/sirupsen/logrus@v1.9.3 golang.org/x/crypto@v0.57.0 \
    golang.org/x/net@v0.60.0 golang.org/x/text@v0.42.0
build_tool github.com/projectdiscovery/httpx v1.12.0 ./cmd/httpx httpx \
    github.com/klauspost/compress@v1.18.7 golang.org/x/net@v0.60.0
build_tool github.com/projectdiscovery/interactsh v1.4.1 ./cmd/interactsh-client interactsh-client \
    github.com/klauspost/compress@v1.18.7 golang.org/x/net@v0.60.0
build_tool github.com/projectdiscovery/katana v1.8.0 ./cmd/katana katana \
    github.com/jackc/pgx/v5@v5.9.0 github.com/klauspost/compress@v1.18.7 \
    golang.org/x/net@v0.60.0
build_tool github.com/projectdiscovery/cvemap v1.0.0 ./cmd/vulnx vulnx \
    github.com/klauspost/compress@v1.18.7 golang.org/x/crypto@v0.57.0 \
    golang.org/x/net@v0.60.0 golang.org/x/text@v0.42.0
build_tool github.com/gitleaks/gitleaks/v8 v8.30.1 . gitleaks \
    github.com/klauspost/compress@v1.18.7 golang.org/x/crypto@v0.57.0 \
    golang.org/x/text@v0.42.0
build_tool github.com/aquasecurity/trivy v0.76.1 ./cmd/trivy trivy \
    github.com/go-jose/go-jose/v4@v4.1.6

# Only /out/bin is copied into the runtime stage.
go clean -cache -modcache
