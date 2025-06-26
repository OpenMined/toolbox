import subprocess

def has_uv():
    try:
        subprocess.run(["uv", "--version"], check=True, capture_output=True)
        return True
    except Exception:
        return False
    
def has_npx():
    try:
        subprocess.run(["npx", "--version"], check=True, capture_output=True)
        return True
    except Exception:
        return False