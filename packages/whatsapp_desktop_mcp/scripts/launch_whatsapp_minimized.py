#!/usr/bin/env python3
import subprocess
import time


def run_applescript(script):
    """Run the given AppleScript code and return the output."""
    process = subprocess.run(
        ["osascript", "-e", script], capture_output=True, text=True
    )
    return process.stdout.strip(), process.returncode


def launch_and_minimize_whatsapp():
    launch_script = """
    tell application "WhatsApp"
        launch
    end tell

    tell application "System Events"
        tell process "WhatsApp"
            repeat until (count of windows) > 0
                delay 0.5
            end repeat
            set value of attribute "AXMinimized" of window 1 to true
        end tell
    end tell
    """

    try:
        result = subprocess.run(
            ["osascript", "-e", launch_script], capture_output=True, timeout=5
        )
        return result.returncode == 0
    except subprocess.TimeoutExpired:
        print("AppleScript timed out after 5 seconds")
        return False


def get_window_count():
    check_windows_script = """
    tell application "System Events"
        count windows of process "WhatsApp"
    end tell
    """
    output, _ = run_applescript(check_windows_script)
    try:
        return int(output)
    except ValueError:
        return 0


def main():
    max_attempts = 5
    for attempt in range(1, max_attempts + 1):
        print(f"Attempt {attempt} to launch and minimize WhatsApp...")

        if launch_and_minimize_whatsapp():
            time.sleep(1)  # Give it a moment to update windows
            window_count = get_window_count()
            if window_count > 0:
                print("WhatsApp launched and minimized successfully!")
                break
            else:
                print("No windows found, retrying...")
        else:
            print("Failed to run AppleScript, retrying...")

        time.sleep(1)
    else:
        print(f"Failed to launch and minimize WhatsApp after {max_attempts} attempts.")


if __name__ == "__main__":
    main()
