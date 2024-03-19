#!/bin/bash

# Original Source: https://gist.githubusercontent.com/adamrunner/285746ca0f22b0f2e10192427e0b703c/raw/23ec7544d0377aea3df06e4e9a684935c68bd397/gen_cert.sh
# Original Author: Adam Runner

# Bash shell script for generating self-signed certs. Run this in a folder, as it
# generates a few files. Large portions of this script were taken from the
# following article:
#
# http://usrportage.de/archives/919-Batch-generating-SSL-certificates.html
#
# Additional alterations by: Brad Landers, Lars Froelich
# Dates: 2012-01-27 - 2024-03-12
# usage: ./gen_cert.sh example.com

# Script accepts a single argument, the fqdn for the cert
FILE_NAME="self_signed_cert"
DOMAIN="$1"
if [ -z "$DOMAIN" ]; then
  echo "Usage: $(basename $0) <domain>"
  exit 11
fi

fail_if_error() {
  [ $1 != 0 ] && {
    unset PASSPHRASE
    exit 10
  }
}

# Generate a passphrase
export PASSPHRASE=$(head -c 500 /dev/urandom | tr -dc a-z0-9A-Z | head -c 128; echo)

# Certificate details; replace items in angle brackets with your own info
subj="
C=US
ST=OR
O=Blah
localityName=Portland
commonName=$DOMAIN
organizationalUnitName=Blah Blah
emailAddress=admin@example.com
"

# Generate the server private key
openssl genrsa -des3 -out $FILE_NAME.key -passout env:PASSPHRASE 2048
fail_if_error $?

# Generate the CSR
openssl req \
    -new \
    -batch \
    -subj "$(echo -n "$subj" | tr "\n" "/")" \
    -key $FILE_NAME.key \
    -out $FILE_NAME.csr \
    -passin env:PASSPHRASE
fail_if_error $?
cp $FILE_NAME.key $FILE_NAME.key.org
fail_if_error $?

# Strip the password so we don't have to type it every time we restart Apache
openssl rsa -in $FILE_NAME.key.org -out $FILE_NAME.key -passin env:PASSPHRASE
fail_if_error $?

# Generate the cert (good for 100 years)
openssl x509 -req -days 36500 -in $FILE_NAME.csr -signkey $FILE_NAME.key -out $FILE_NAME.crt
fail_if_error $?

echo "Success! Files created: $FILE_NAME.key, $FILE_NAME.csr, and $FILE_NAME.crt"
