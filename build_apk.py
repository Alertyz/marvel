#!/usr/bin/env python3
"""
Build APK for Marvel Comic Reader.

Creates an Android APK that wraps the web app in a WebView
with self-signed certificate support for Samsung Galaxy S23+ and others.

Requirements:
  - JDK 17+ installed (https://adoptium.net/)
  - Internet connection (first run downloads ~400MB of build tools)

Usage:
  python build_apk.py              # Auto-detect server IP
  python build_apk.py --ip 192.168.1.50  # Specify IP
  python build_apk.py --port 9000  # Custom port
"""
import os
import platform
import re
import shutil
import socket
import subprocess
import sys
import urllib.request
import zipfile
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
ANDROID_DIR = BASE_DIR / "android-app"
BUILD_TOOLS_DIR = BASE_DIR / ".build-tools"
APK_OUTPUT = BASE_DIR / "web" / "marvel-reader.apk"

GRADLE_VERSION = "8.5"
IS_WINDOWS = platform.system() == "Windows"

GRADLE_URL = f"https://services.gradle.org/distributions/gradle-{GRADLE_VERSION}-bin.zip"
GRADLE_DIR = BUILD_TOOLS_DIR / f"gradle-{GRADLE_VERSION}"
GRADLE_BIN = GRADLE_DIR / "bin" / ("gradle.bat" if IS_WINDOWS else "gradle")

ANDROID_SDK_DIR = BUILD_TOOLS_DIR / "android-sdk"

# Android cmdline-tools download URLs per platform
_CMDLINE_URLS = {
    "Windows": "https://dl.google.com/android/repository/commandlinetools-win-11076708_latest.zip",
    "Darwin": "https://dl.google.com/android/repository/commandlinetools-mac-11076708_latest.zip",
    "Linux": "https://dl.google.com/android/repository/commandlinetools-linux-11076708_latest.zip",
}
CMDLINE_TOOLS_URL = _CMDLINE_URLS.get(platform.system(), _CMDLINE_URLS["Linux"])

SDKMANAGER = (
    ANDROID_SDK_DIR / "cmdline-tools" / "latest" / "bin" /
    ("sdkmanager.bat" if IS_WINDOWS else "sdkmanager")
)

SDK_PACKAGES = ["platforms;android-34", "build-tools;34.0.0", "platform-tools"]


def get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "192.168.1.100"


def find_java():
    """Find Java 17+ installation."""
    # Check JAVA_HOME
    java_home = os.environ.get("JAVA_HOME", "")
    if java_home:
        ext = ".exe" if IS_WINDOWS else ""
        java = Path(java_home) / "bin" / f"java{ext}"
        if java.exists():
            return str(java)

    # Check PATH
    try:
        result = subprocess.run(
            ["java", "-version"], capture_output=True, text=True, timeout=10
        )
        if result.returncode == 0:
            # Check version >= 17
            version_line = result.stderr.split("\n")[0]
            match = re.search(r'"(\d+)', version_line)
            if match:
                major = int(match.group(1))
                if major >= 17:
                    return "java"
                print(f"  ⚠  Java {major} encontrado, mas precisa ser 17+")
                return None
            return "java"
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass

    return None


def download_and_extract(url, dest_dir, desc):
    """Download a zip and extract it."""
    dest_dir.mkdir(parents=True, exist_ok=True)
    zip_path = dest_dir / "download.zip"

    print(f"  ⬇  Baixando {desc}...")
    print(f"     {url}")

    try:
        urllib.request.urlretrieve(url, zip_path)
    except Exception as e:
        print(f"  ✗ Erro ao baixar: {e}")
        sys.exit(1)

    print(f"  📦 Extraindo...")
    with zipfile.ZipFile(zip_path, "r") as z:
        z.extractall(dest_dir)

    zip_path.unlink()
    print(f"  ✓ {desc} pronto")


def setup_gradle():
    """Download Gradle if not present. Returns path to gradle binary."""
    if GRADLE_BIN.exists():
        print(f"  ✓ Gradle {GRADLE_VERSION} já instalado")
        return str(GRADLE_BIN)

    print("\n── Baixando Gradle ──")
    download_and_extract(GRADLE_URL, BUILD_TOOLS_DIR, f"Gradle {GRADLE_VERSION}")

    # Make executable on Unix
    if not IS_WINDOWS:
        GRADLE_BIN.chmod(0o755)

    return str(GRADLE_BIN)


def setup_android_sdk():
    """Download and configure Android SDK. Returns SDK path."""
    if not SDKMANAGER.exists():
        print("\n── Baixando Android SDK ──")
        temp_dir = ANDROID_SDK_DIR / "_temp"
        download_and_extract(CMDLINE_TOOLS_URL, temp_dir, "Android Command Line Tools")

        # Move to correct structure: android-sdk/cmdline-tools/latest/
        src = temp_dir / "cmdline-tools"
        dest = ANDROID_SDK_DIR / "cmdline-tools" / "latest"
        dest.parent.mkdir(parents=True, exist_ok=True)

        if dest.exists():
            shutil.rmtree(dest)
        shutil.move(str(src), str(dest))
        shutil.rmtree(temp_dir, ignore_errors=True)

        # Make executable on Unix
        if not IS_WINDOWS:
            SDKMANAGER.chmod(0o755)

    # Accept licenses
    print("  📋 Aceitando licenças do SDK...")
    subprocess.run(
        [str(SDKMANAGER), "--licenses", f"--sdk_root={ANDROID_SDK_DIR}"],
        input="y\n" * 20,
        text=True,
        capture_output=True,
    )

    # Install required packages
    for pkg in SDK_PACKAGES:
        print(f"  📦 Instalando {pkg}...")
        subprocess.run(
            [str(SDKMANAGER), pkg, f"--sdk_root={ANDROID_SDK_DIR}"],
            capture_output=True,
            text=True,
        )

    print("  ✓ Android SDK configurado")
    return str(ANDROID_SDK_DIR)


def configure_project(server_ip, server_port):
    """Set server URL in Android project and copy icons."""
    # Update strings.xml with server URL
    strings_file = ANDROID_DIR / "app" / "src" / "main" / "res" / "values" / "strings.xml"
    content = strings_file.read_text(encoding="utf-8")
    content = re.sub(
        r'<string name="server_url">.*?</string>',
        f'<string name="server_url">https://{server_ip}:{server_port}</string>',
        content,
    )
    strings_file.write_text(content, encoding="utf-8")
    print(f"  ✓ Server URL: https://{server_ip}:{server_port}")

    # Copy app icon from web/
    icon_src = BASE_DIR / "web" / "icon-192.png"
    if icon_src.exists():
        for density in ["mdpi", "hdpi", "xhdpi", "xxhdpi", "xxxhdpi"]:
            icon_dir = ANDROID_DIR / "app" / "src" / "main" / "res" / f"mipmap-{density}"
            icon_dir.mkdir(parents=True, exist_ok=True)
            shutil.copy2(str(icon_src), str(icon_dir / "ic_launcher.png"))
        print("  ✓ Ícone copiado")
    else:
        print("  ⚠  web/icon-192.png não encontrado — usando ícone padrão")

    # Write local.properties with SDK path
    local_props = ANDROID_DIR / "local.properties"
    sdk_path = str(ANDROID_SDK_DIR).replace("\\", "/")
    local_props.write_text(f"sdk.dir={sdk_path}\n", encoding="utf-8")
    print("  ✓ local.properties criado")


def build_apk(gradle_bin):
    """Run Gradle build and copy APK output."""
    print("\n── Compilando APK ──")
    print("  (Isso pode levar alguns minutos na primeira vez...)")

    env = os.environ.copy()
    env["ANDROID_HOME"] = str(ANDROID_SDK_DIR)
    env["ANDROID_SDK_ROOT"] = str(ANDROID_SDK_DIR)

    result = subprocess.run(
        [gradle_bin, "-p", str(ANDROID_DIR), "assembleDebug", "--no-daemon"],
        env=env,
    )

    if result.returncode != 0:
        print("\n  ✗ Build falhou!")
        print("  Verifique se o JDK 17+ está instalado corretamente.")
        sys.exit(1)

    # Find the output APK
    apk_dir = ANDROID_DIR / "app" / "build" / "outputs" / "apk" / "debug"
    apks = list(apk_dir.glob("*.apk"))
    if not apks:
        print("  ✗ APK não encontrado no output!")
        sys.exit(1)

    # Copy to web/ for serving
    shutil.copy2(str(apks[0]), str(APK_OUTPUT))
    size_mb = APK_OUTPUT.stat().st_size / (1024 * 1024)
    print(f"\n  ✓ APK gerado: web/marvel-reader.apk ({size_mb:.1f} MB)")


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Build Marvel Reader APK")
    parser.add_argument("--ip", default=None, help="Server IP address")
    parser.add_argument("--port", default=8000, type=int, help="Server port")
    args = parser.parse_args()

    server_ip = args.ip or get_local_ip()

    print()
    print("  ╔══════════════════════════════════════════╗")
    print("  ║     Marvel Reader — APK Builder          ║")
    print("  ╠══════════════════════════════════════════╣")
    print(f"  ║  Server: https://{server_ip}:{args.port:<5}        ║")
    print(f"  ║  Target: Samsung Galaxy S23+ (arm64)    ║")
    print("  ╚══════════════════════════════════════════╝")

    # 1. Check Java
    print("\n── Verificando Java ──")
    java = find_java()
    if not java:
        print()
        print("  ✗ JDK 17+ não encontrado!")
        print()
        print("  Para instalar:")
        print("  1. Acesse https://adoptium.net/")
        print("  2. Baixe 'Temurin 17 (LTS)' para Windows x64")
        print("  3. Instale com a opção 'Set JAVA_HOME' marcada")
        print("  4. Reinicie o terminal e execute novamente")
        sys.exit(1)
    print(f"  ✓ Java encontrado")

    # 2. Setup Gradle
    gradle_bin = setup_gradle()

    # 3. Setup Android SDK
    setup_android_sdk()

    # 4. Configure project
    print("\n── Configurando projeto ──")
    configure_project(server_ip, args.port)

    # 5. Build
    build_apk(gradle_bin)

    print()
    print("  ╔══════════════════════════════════════════╗")
    print("  ║  ✓ APK pronto para instalar!             ║")
    print("  ╠══════════════════════════════════════════╣")
    print("  ║                                          ║")
    print("  ║  Para instalar no celular:               ║")
    print("  ║  1. Execute: python run.py               ║")
    print(f"  ║  2. No celular, acesse:                  ║")
    print(f"  ║     https://{server_ip}:{args.port:<5}            ║")
    print("  ║  3. Toque em 📲 → Baixar APK             ║")
    print("  ║  4. Abra o APK baixado e instale         ║")
    print("  ║                                          ║")
    print("  ║  Ou transfira o arquivo diretamente:     ║")
    print("  ║  web/marvel-reader.apk                   ║")
    print("  ╚══════════════════════════════════════════╝")
    print()


if __name__ == "__main__":
    main()
