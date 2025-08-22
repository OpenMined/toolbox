import json
import sys
from pathlib import Path


def main():
    """Test script that processes events from stdin and writes output for testing"""

    # Read events from stdin (JSON format with "events" wrapper)
    events_data = sys.stdin.read().strip()
    if not events_data:
        events = []
    else:
        data = json.loads(events_data)
        events = data.get("events", [])

    # Process the events
    print(f"RECEIVED_EVENTS_COUNT: {len(events)}")

    for i, event in enumerate(events):
        print(f"EVENT_{i}_ID: {event.get('id', 'unknown')}")
        print(f"EVENT_{i}_NAME: {event.get('name', 'unknown')}")
        print(f"EVENT_{i}_SOURCE: {event.get('source', 'unknown')}")
        print(f"EVENT_{i}_DATA: {json.dumps(event.get('data', {}))}")

    # Write a summary file for verification
    # Use environment variable for output path, fallback to default
    import os

    output_path = os.environ.get("TEST_SCRIPT_OUTPUT_FILE")
    if output_path:
        summary_file = Path(output_path)
        summary_file.parent.mkdir(parents=True, exist_ok=True)
    else:
        # Fallback for manual testing
        output_dir = Path("/tmp/toolbox_test_output")
        output_dir.mkdir(exist_ok=True)
        summary_file = output_dir / "test_script_output.json"
    summary = {
        "events_received": len(events),
        "event_ids": [e.get("id") for e in events],
        "event_names": [e.get("name") for e in events],
        "event_sources": [e.get("source") for e in events],
    }

    with open(summary_file, "w") as f:
        json.dump(summary, f, indent=2)

    print(f"SUMMARY_FILE: {summary_file}")
    print("SCRIPT_COMPLETED_SUCCESSFULLY")


if __name__ == "__main__":
    main()
