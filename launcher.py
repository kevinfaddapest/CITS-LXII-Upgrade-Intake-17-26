import os
import subprocess
import time
import socket
import sys

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "system2.settings")

def is_port_open(host, port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(1)
        return sock.connect_ex((host, port)) == 0

manage_py = os.path.join(BASE_DIR, 'manage.py')

if not os.path.exists(manage_py):
    print(f"ERROR: manage.py not found at {manage_py}")
    sys.exit(1)

print("Starting Django from:", BASE_DIR)

proc = subprocess.Popen(
    [sys.executable, 'manage.py', 'runserver', '127.0.0.1:8000'],
    cwd=BASE_DIR
)

start_time = time.time()
timeout = 30
while not is_port_open('127.0.0.1', 8000):
    if time.time() - start_time > timeout:
        print("ERROR: Django server did not start within timeout.")
        proc.terminate()
        sys.exit(1)
    time.sleep(1)

print("Django server started successfully.")

try:
    proc.wait()
except KeyboardInterrupt:
    proc.terminate()
