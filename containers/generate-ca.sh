#!/bin/sh
set -eu
umask 077
cert_dir="${1:?certificate directory required}"
mkdir -p "$cert_dir"
openssl ecparam -name prime256v1 -genkey -noout -out "$cert_dir/ca.key"
openssl req -x509 -new -key "$cert_dir/ca.key" -out "$cert_dir/ca.crt" \
    -days 365 -subj "/C=US/ST=CA/O=Security Testing/CN=Testing Root CA" \
    -addext "basicConstraints=critical,CA:TRUE" \
    -addext "keyUsage=critical,digitalSignature,keyEncipherment,keyCertSign"
openssl pkcs12 -export -out "$cert_dir/ca.p12" -inkey "$cert_dir/ca.key" \
    -in "$cert_dir/ca.crt" -passout pass: -name "Testing Root CA"
chmod 600 "$cert_dir/ca.key" "$cert_dir/ca.p12"
chmod 644 "$cert_dir/ca.crt"
