#!/bin/bash
set -e

# Redis SSL Certificate Generation Script
# This script generates self-signed SSL certificates for Redis cluster testing
# Supports both mkcert (preferred) and openssl methods

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
SSL_CERTS_DIR="$PROJECT_ROOT/ssl-certs"

echo "=========================================="
echo "Redis SSL Certificate Generator"
echo "=========================================="
echo ""

# Check if mkcert is available
if command -v mkcert &> /dev/null; then
    echo "✓ mkcert found - using mkcert (recommended)"
    USE_MKCERT=true
else
    echo "✗ mkcert not found - falling back to openssl"
    echo "  Install mkcert for easier certificate management:"
    echo "  - macOS:   brew install mkcert"
    echo "  - Linux:   See https://github.com/FiloSottile/mkcert#installation"
    echo ""
    USE_MKCERT=false
fi

# Create ssl-certs directory
mkdir -p "$SSL_CERTS_DIR"
cd "$SSL_CERTS_DIR"

if [ "$USE_MKCERT" = true ]; then
    echo ""
    echo "Generating certificates with mkcert..."
    echo "---------------------------------------"
    
    # Generate certificates for all Redis nodes
    mkcert -cert-file redis.crt -key-file redis.key \
        redis-node-0 \
        redis-node-1 \
        redis-node-2 \
        redis-node-0-ssl \
        redis-node-1-ssl \
        redis-node-2-ssl \
        localhost \
        127.0.0.1 \
        ::1
    
    # Copy the mkcert root CA
    cp "$(mkcert -CAROOT)/rootCA.pem" ca.crt
    
    echo "✓ Certificates generated with mkcert"
else
    echo ""
    echo "Generating certificates with openssl..."
    echo "---------------------------------------"
    
    # Generate CA key and certificate
    echo "1. Generating CA certificate..."
    openssl genrsa -out ca.key 4096 2>/dev/null
    openssl req -x509 -new -nodes -key ca.key -sha256 -days 3650 -out ca.crt \
        -subj "/C=US/ST=State/L=City/O=Redis-Test/CN=Redis-CA" 2>/dev/null
    
    # Generate server key
    echo "2. Generating server private key..."
    openssl genrsa -out redis.key 4096 2>/dev/null
    
    # Create OpenSSL config for SAN
    cat > redis.cnf <<EOF
[req]
default_bits = 4096
prompt = no
default_md = sha256
req_extensions = req_ext
distinguished_name = dn

[dn]
C = US
ST = State
L = City
O = Redis-Test
CN = redis-node-0

[req_ext]
subjectAltName = @alt_names

[alt_names]
DNS.1 = redis-node-0
DNS.2 = redis-node-1
DNS.3 = redis-node-2
DNS.4 = redis-node-0-ssl
DNS.5 = redis-node-1-ssl
DNS.6 = redis-node-2-ssl
DNS.7 = localhost
IP.1 = 127.0.0.1
EOF
    
    # Generate certificate signing request
    echo "3. Generating certificate signing request..."
    openssl req -new -key redis.key -out redis.csr -config redis.cnf 2>/dev/null
    
    # Sign the certificate with our CA
    echo "4. Signing certificate with CA..."
    openssl x509 -req -in redis.csr -CA ca.crt -CAkey ca.key \
        -CAcreateserial -out redis.crt -days 3650 -sha256 \
        -extensions req_ext -extfile redis.cnf 2>/dev/null
    
    # Clean up temporary files
    rm -f redis.csr redis.cnf ca.srl
    
    echo "✓ Certificates generated with openssl"
fi

# Set proper permissions
chmod 644 redis.crt ca.crt
chmod 600 redis.key ca.key 2>/dev/null || chmod 600 redis.key

echo ""
echo "=========================================="
echo "Certificate Generation Complete!"
echo "=========================================="
echo ""
echo "Generated files in $SSL_CERTS_DIR:"
ls -lh "$SSL_CERTS_DIR"
echo ""
echo "Certificates valid for:"
echo "  - redis-node-0, redis-node-1, redis-node-2"
echo "  - redis-node-0-ssl, redis-node-1-ssl, redis-node-2-ssl"
echo "  - localhost"
echo "  - 127.0.0.1"
echo ""
echo "Next steps:"
echo "  1. Start the SSL-enabled cluster: docker compose --profile ssl up -d"
echo "  2. Wait for initialization: sleep 10"
echo "  3. Verify cluster: docker compose exec redis-node-0-ssl redis-cli -c -p 6379 cluster info"
echo "  4. Test SSL connection in Django admin panel (redis-cluster-ssl instance)"
echo ""
echo "To use the regular non-SSL cluster instead:"
echo "  docker compose up -d  (no --profile flag needed)"
echo ""
