"""Kill all running chrome.exe and chromedriver.exe processes."""
import subprocess

for proc in ("chromedriver.exe", "chrome.exe"):
    try:
        result = subprocess.run(
            ["taskkill", "/F", "/IM", proc],
            capture_output=True, text=True,
        )
        if result.returncode == 0:
            print(f"[OK] {proc} encerrado")
        else:
            print(f"[--] {proc} nao encontrado")
    except Exception as e:
        print(f"[ERRO] {proc}: {e}")
