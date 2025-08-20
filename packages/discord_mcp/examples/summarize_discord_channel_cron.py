import subprocess
import sys


# Build the command
cmd = ["claude", "--write", "--mcp"]

result = subprocess.run(cmd, capture_output=True, text=True, check=True)
