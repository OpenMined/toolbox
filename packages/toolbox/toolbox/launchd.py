import os
import platform
import shutil
from pathlib import Path


def get_launchd_path() -> Path:
    if platform.system() != "Darwin":
        raise RuntimeError("launchd is only available on macOS")

    if not shutil.which("launchctl"):
        raise RuntimeError("launchctl command not found")

    user_agents = Path.home() / "Library" / "LaunchAgents"
    if not user_agents.exists():
        raise RuntimeError(f"LaunchAgents directory not found at {user_agents}")

    return user_agents / "com.toolbox.daemon.plist"


user = os.environ["USER"]
LAUNCHD_PLIST = f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.toolbox.daemon</string>
    <key>ProgramArguments</key>
    <array>
        <string>/Users/{user}/.local/bin/tb</string>
        <string>daemon</string>
        <string>run-foreground</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>StandardOutPath</key>
    <string>/tmp/toolbox-daemon.out</string>
    <key>StandardErrorPath</key>
    <string>/tmp/toolbox-daemon.err</string>
</dict>
</plist>"""
