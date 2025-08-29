#!/usr/bin/env python3
"""
Process Obsidian file events to extract and track TODOs using Claude.
"""

import subprocess
from datetime import datetime
from pathlib import Path

import toolbox_events

# Phase 1: Ingest events and deduplicate files
events = toolbox_events.get_events()
file_paths = list(
    set(
        event.data.get("path")
        for event in events
        if event.name in ["file.created", "file.modified"] and event.data.get("path")
    )
)

if not file_paths:
    print("No file events to process")
    exit()

# Phase 2: Build prompt for Claude
date_str = datetime.now().strftime("%Y%m%d")
output_path = Path.home() / f"todos-{date_str}.md"

# Read existing TODOs if the file exists
existing_todos = ""
if output_path.exists():
    existing_todos = f"""
Any TODO's you find should be merged with the following existing TODOs:
```markdown
{output_path.read_text()}
```
Merge any new TODOs with the existing ones above, merging the context and avoiding duplicates.
"""

prompt = f"""
You are a helpful assistant that analyzes and manages TODOs from Obsidian files.
Analyze the following Obsidian note files for TODO items, tasks, and action items.
Extract any important todos, tasks, or action items that need attention.
Side notes, and tasks that are not actionable are not important and can be ignored.
{existing_todos}
New files to analyze:
{chr(10).join(f"- {path}" for path in file_paths)}

For each file:
1. Read the file directly from disk using the Read tool (these are absolute paths)
2. Look for TODO items, tasks, checkboxes (- [ ]), or any action items
3. Extract the context around each todo to understand what needs to be done
4. Categorize by urgency if mentioned (urgent, high priority, etc.)

Output a markdown summary with the following structure:

```markdown
# TODOs from Obsidian - {date_str}

## High Priority
- [ ] List high priority items here with context
    - Some optional important context can be provided here, but it is not required.
    - [ ] optional subtasks can be provided here, but it is not required.

## Medium Priority
- [ ] List medium priority items here

## Low Priority / Unspecified
- [ ] List other items here
```

For each TODO, include:
- The task description
- Which file it came from (as a link or reference. In Obsidian the [relative_path] is the link)
- Any relevant context or deadline

If a file has been deleted or can't be read, skip it.
If no TODOs are found, output "No TODOs found in the processed files."
Focus on actionable items - ignore completed tasks (- [x]) or general notes.

IMPORTANT: Just print the markdown result to stdout, don't write any files, and don't include any other text in the output.
"""

# Phase 3: Run Claude and write output
print(f"Processing {len(file_paths)} file(s) for TODOs...")
result = subprocess.run(
    ["claude", prompt, "--allowedTools", "Read", "--print"],
    capture_output=True,
    text=True,
)

if result.returncode == 0:
    output_path.write_text(result.stdout)
    print(f"✅ TODOs extracted and saved to {output_path}")
    print("\n--- TODO Summary ---")
    print(result.stdout)
else:
    print(f"Error running Claude: {result.stderr}")

# Save output to a file
output_path.write_text(result.stdout)
print(f"✅ TODOs extracted and saved to {output_path}")
