#!/usr/bin/env python3
"""Marvel Comic Reader — Start the server."""
import socket
import uvicorn
from server.config import HOST, PORT


def get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"


if __name__ == "__main__":
    ip = get_local_ip()

    print()
    print("  ╔═══════════════════════════════════════════════╗")
    print("  ║         Marvel Comic Reader                   ║")
    print("  ╠═══════════════════════════════════════════════╣")
    print(f"  ║  Local:   http://localhost:{PORT}              ║")
    print(f"  ║  Rede:    http://{ip:<15}:{PORT}        ║")
    print("  ╠═══════════════════════════════════════════════╣")
    print("  ║  📖 PC:      Abra o link acima no navegador   ║")
    print("  ║  📱 Celular: Conecte o app ao IP da rede      ║")
    print("  ╚═══════════════════════════════════════════════╝")
    print()

    uvicorn.run("server.app:app", host=HOST, port=PORT)
