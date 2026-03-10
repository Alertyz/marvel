#!/usr/bin/env python3
"""Marvel Comic Reader — Start the server with HTTPS + HTTP for PWA and remote access."""
import socket
import ssl
import sys
import threading
from pathlib import Path

import uvicorn

CERT_DIR = Path(__file__).resolve().parent / ".certs"
CERT_FILE = CERT_DIR / "cert.pem"
KEY_FILE = CERT_DIR / "key.pem"


def get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "???"


def ensure_certs(ip: str):
    """Generate a self-signed cert (valid 10 years) if none exists."""
    if CERT_FILE.exists() and KEY_FILE.exists():
        return
    try:
        from cryptography import x509
        from cryptography.x509.oid import NameOID
        from cryptography.hazmat.primitives import hashes, serialization
        from cryptography.hazmat.primitives.asymmetric import rsa
        import datetime
        import ipaddress
    except ImportError:
        print("  ⚠  'cryptography' não instalada. Instalando...")
        import subprocess
        subprocess.check_call([sys.executable, "-m", "pip", "install", "cryptography"])
        from cryptography import x509
        from cryptography.x509.oid import NameOID
        from cryptography.hazmat.primitives import hashes, serialization
        from cryptography.hazmat.primitives.asymmetric import rsa
        import datetime
        import ipaddress

    CERT_DIR.mkdir(exist_ok=True)

    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)

    san_entries = [
        x509.DNSName("localhost"),
    ]
    try:
        san_entries.append(x509.IPAddress(ipaddress.ip_address(ip)))
    except ValueError:
        pass

    subject = issuer = x509.Name([
        x509.NameAttribute(NameOID.COMMON_NAME, "Marvel Comic Reader"),
    ])
    cert = (
        x509.CertificateBuilder()
        .subject_name(subject)
        .issuer_name(issuer)
        .public_key(key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(datetime.datetime.utcnow())
        .not_valid_after(datetime.datetime.utcnow() + datetime.timedelta(days=3650))
        .add_extension(x509.SubjectAlternativeName(san_entries), critical=False)
        .sign(key, hashes.SHA256())
    )

    KEY_FILE.write_bytes(
        key.private_bytes(serialization.Encoding.PEM,
                          serialization.PrivateFormat.TraditionalOpenSSL,
                          serialization.NoEncryption())
    )
    CERT_FILE.write_bytes(cert.public_bytes(serialization.Encoding.PEM))
    print("  ✓ Certificado SSL gerado em .certs/")


if __name__ == "__main__":
    ip = get_local_ip()
    ensure_certs(ip)

    print()
    print("  ╔═══════════════════════════════════════════════╗")
    print("  ║         Marvel Comic Reader                   ║")
    print("  ╠═══════════════════════════════════════════════╣")
    print(f"  ║  HTTPS:   https://localhost:8000              ║")
    print(f"  ║  HTTPS:   https://{ip:<15}:8000        ║")
    print(f"  ║  HTTP:    http://{ip:<15}:8080         ║")
    print("  ╠═══════════════════════════════════════════════╣")
    print("  ║  📱 CELULAR — Duas opções:                     ║")
    print("  ║                                               ║")
    print("  ║  Opção A: APK (Recomendado)                   ║")
    print("  ║  1. Execute: python build_apk.py              ║")
    print("  ║  2. Acesse o site no celular                  ║")
    print("  ║  3. Toque em 📲 → Baixar APK                  ║")
    print("  ║                                               ║")
    print("  ║  Opção B: Instalar via navegador              ║")
    print("  ║  1. Acesse o link da Rede no celular          ║")
    print("  ║  2. Aceite o aviso de certificado             ║")
    print("  ║  3. Menu ⋮ → Instalar app                     ║")
    print("  ╠═══════════════════════════════════════════════╣")
    print("  ║  🌐 GitHub Pages: use HTTP (porta 8080) como  ║")
    print("  ║     servidor de imagens para evitar problemas  ║")
    print("  ║     com certificado SSL.                      ║")
    print("  ╚═══════════════════════════════════════════════╝")
    print()

    # Start HTTP server on port 8080 in background thread (for GitHub Pages cross-origin access)
    def run_http():
        uvicorn.run(
            "server.app:app",
            host="0.0.0.0",
            port=8080,
            log_level="warning",
        )

    http_thread = threading.Thread(target=run_http, daemon=True)
    http_thread.start()

    # Start HTTPS server on port 8000 (main, for local PWA + mobile)
    uvicorn.run(
        "server.app:app",
        host="0.0.0.0",
        port=8000,
        ssl_keyfile=str(KEY_FILE),
        ssl_certfile=str(CERT_FILE),
    )
