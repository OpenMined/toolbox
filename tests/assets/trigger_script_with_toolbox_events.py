#!/usr/bin/env python3
"""Test trigger script that uses toolbox_events to consume events"""

import json
import os
import sys
from pathlib import Path


def main():
    """Process events using toolbox_events library"""

    # Import toolbox_events
    try:
        from toolbox_events import get_events

        print("SUCCESS: Imported toolbox_events", file=sys.stderr)
    except ImportError as e:
        print(f"ERROR: Failed to import toolbox_events: {e}", file=sys.stderr)
        sys.exit(1)

    # Get events using the library
    try:
        events = get_events()
        print(f"RECEIVED_EVENTS_COUNT: {len(events)}")

        # Process each event
        processed_events = []
        for i, event in enumerate(events):
            print(f"EVENT_{i}_NAME: {event.name}")
            print(f"EVENT_{i}_SOURCE: {event.source}")
            print(f"EVENT_{i}_DATA: {json.dumps(event.data)}")
            print(f"EVENT_{i}_TIMESTAMP: {event.timestamp.isoformat()}")

            processed_events.append(
                {
                    "name": event.name,
                    "source": event.source,
                    "data": event.data,
                    "timestamp": event.timestamp.isoformat(),
                }
            )

        # Write marker file to confirm execution
        output_path = os.environ.get("TEST_OUTPUT_FILE")
        if output_path:
            output_file = Path(output_path)
            output_file.parent.mkdir(parents=True, exist_ok=True)

            result = {
                "success": True,
                "events_count": len(events),
                "events": processed_events,
                "using_toolbox_events": True,
            }

            with open(output_file, "w") as f:
                json.dump(result, f, indent=2)

            print(f"MARKER_FILE: {output_file}")

        print("SCRIPT_COMPLETED_SUCCESSFULLY")

    except Exception as e:
        print(f"ERROR: Failed to process events: {e}", file=sys.stderr)
        import traceback

        traceback.print_exc(file=sys.stderr)

        # Write error marker if output path is set
        output_path = os.environ.get("TEST_OUTPUT_FILE")
        if output_path:
            output_file = Path(output_path)
            output_file.parent.mkdir(parents=True, exist_ok=True)

            error_result = {
                "success": False,
                "error": str(e),
                "using_toolbox_events": True,
            }

            with open(output_file, "w") as f:
                json.dump(error_result, f, indent=2)

        sys.exit(1)


if __name__ == "__main__":
    main()
