#!/usr/bin/env python3
"""Marvel Comic Reader — Start the server."""
import socket
import uvicorn


def get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "???"


if __name__ == "__main__":
    ip = get_local_ip()
    print()
    print("  ╔══════════════════════════════════════╗")
    print("  ║       Marvel Comic Reader            ║")
    print("  ╠══════════════════════════════════════╣")
    print(f"  ║  Local:   http://localhost:8000      ║")
    print(f"  ║  Rede:    http://{ip}:8000  ║")
    print("  ╚══════════════════════════════════════╝")
    print()

    uvicorn.run("server.app:app", host="0.0.0.0", port=8000, reload=True)
