import sys
import subprocess

# Just install dependencies.
subprocess.check_call(
    [sys.executable, "-m", "pip", "install", "-r", "requirements.txt"]
)
