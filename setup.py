import sys
import subprocess

# Just install dependencies. Actual auth setup has moved to src.authentication.TwitchOAuth2Helper.setup().
subprocess.check_call(
    [sys.executable, "-m", "pip", "install", "-r", "requirements.txt"]
)
