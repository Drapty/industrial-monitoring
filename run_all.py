import os
import subprocess
import sys
import time

ROOT = os.path.dirname(os.path.abspath(__file__))
VENV = os.path.join(ROOT, ".venv")
PYTHON = os.path.join(VENV, "Scripts", "python.exe")


def ensure_venv():
    if not os.path.exists(PYTHON):
        print("Creating virtual environment...")
        subprocess.run([sys.executable, "-m", "venv", VENV], check=True)


def install_requirements():
    if not os.path.exists(os.path.join(ROOT, "requirements.txt")):
        raise FileNotFoundError("requirements.txt not found")
    print("Installing Python dependencies...")
    subprocess.run([PYTHON, "-m", "pip", "install", "--upgrade", "pip"], check=True)
    subprocess.run([PYTHON, "-m", "pip", "install", "-r", os.path.join(ROOT, "requirements.txt")], check=True)


def start_backend():
    backend_dir = os.path.join(ROOT, "backend")
    env = os.environ.copy()
    env["PYTHONPATH"] = ROOT
    subprocess.Popen([PYTHON, "-m", "uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"], cwd=ROOT, env=env)
    print("Backend started at http://localhost:8000")


def main():
    ensure_venv()
    install_requirements()
    start_backend()
    print("The app is running. Open http://localhost:8000 in the browser.")
    print("To stop the app, close this terminal window.")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Stopping...")


if __name__ == "__main__":
    main()
