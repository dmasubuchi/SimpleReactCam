"""
Script to run all three backend services locally for development and testing.
"""
import os
import subprocess
import sys
import time
from pathlib import Path

SERVICES = [
    {"name": "api-gateway", "port": 8080},
    {"name": "image-processor", "port": 8081},
    {"name": "message-generator", "port": 8082},
]

BASE_DIR = Path(__file__).parent.absolute()


def check_venv():
    """Check if running in a virtual environment."""
    if not hasattr(sys, 'real_prefix') and not (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
        print("Error: Not running in a virtual environment.")
        print("Please activate the virtual environment first:")
        print("  source venv/bin/activate")
        sys.exit(1)


def install_requirements():
    """Install requirements for all services."""
    for service in SERVICES:
        service_dir = BASE_DIR / service["name"]
        req_file = service_dir / "requirements.txt"
        
        if req_file.exists():
            print(f"Installing requirements for {service['name']}...")
            subprocess.run(
                [sys.executable, "-m", "pip", "install", "-r", str(req_file)],
                check=True
            )


def run_services():
    """Run all services using uvicorn."""
    processes = []
    
    try:
        for service in SERVICES:
            service_dir = BASE_DIR / service["name"]
            main_file = service_dir / "src" / "main.py"
            
            if not main_file.exists():
                print(f"Error: {main_file} does not exist.")
                continue
            
            print(f"Starting {service['name']} on port {service['port']}...")
            
            env = os.environ.copy()
            
            cmd = [
                sys.executable, "-m", "uvicorn",
                f"src.main:app",
                "--host", "0.0.0.0",
                "--port", str(service["port"]),
                "--reload"
            ]
            
            process = subprocess.Popen(
                cmd,
                cwd=str(service_dir),
                env=env
            )
            
            processes.append((service["name"], process))
            print(f"{service['name']} started with PID {process.pid}")
            
            time.sleep(1)
        
        print("\nAll services are running. Press Ctrl+C to stop.\n")
        
        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\nStopping all services...")
        
    finally:
        for name, process in processes:
            print(f"Stopping {name}...")
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                print(f"Killing {name} (did not terminate gracefully)...")
                process.kill()


if __name__ == "__main__":
    check_venv()
    install_requirements()
    run_services()
