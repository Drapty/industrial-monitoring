import os
import subprocess
import sys
import time

ROOT = os.path.dirname(os.path.abspath(__file__))



def install_requirements():
    if not os.path.exists(os.path.join(ROOT, "requirements.txt")):
        raise FileNotFoundError("requirements.txt not found . The app is stopped")
    if sys.version_info < (3, 7):
        raise RuntimeError("Python 3.7 or higher is required")
        print("Installing Python dependencies...")
        subprocess.run([sys.executable, "-m", "pip", "install", "--upgrade", "pip"], check=True)
        subprocess.run([sys.executable, "-m", "pip", "install", "-r", os.path.join(ROOT, "requirements.txt")], check=True)
    else:
        print("Python version is sufficient. Skipping installation of dependencies.")


def start_backend():
    backend_dir = os.path.join(ROOT, "backend")
    env = os.environ.copy()
    env["PYTHONPATH"] = ROOT
    subprocess.Popen(["python",
                       "-m",
                       "uvicorn", 
                       "backend.main:app", 
                       "--host" , "0.0.0.0", 
                       "--port", 
                       "8000"],
                     cwd=ROOT, env=env
                     )
    
    print("Backend started at http://localhost:8000")
    
                    


def main():

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
