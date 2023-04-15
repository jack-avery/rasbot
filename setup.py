import sys
import subprocess

# Just install dependencies.
subprocess.call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
