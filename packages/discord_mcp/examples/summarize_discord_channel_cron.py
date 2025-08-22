import subprocess
from pathlib import Path

out_path = (Path.home() / "Documents" / "discord_summaries").resolve()
out_path.mkdir(parents=True, exist_ok=True)

prompt = f"""
Can you call the discord mcp server to get messages from discord using the search_messages endpoint.
I am looking for messages that write about 'effective claude code usage' and write them to a file 
{out_path}/discord_relevant_messages_<date>.json. 

Make sure to read the results and check it they are actually providing insights about
effective claude code usage, I am mostly interested in workflows people use to code faster,
more efficient. Return 50 documents for each query and in the end write a max of 10 documents to the file, fewer documents is
fine but make sure to include only documents that meet the criteria.
Only include messages that actually provide insights into a strategy that makes people more effective. *Dont include anything
from people that are just asking questions or sharing their experiences.*
If you dont get results, try a few similar queries with higher limits (stop after 5 tries).
Use the following format: for the output,
[
    {{
    "message_id": "...",
        "date": "...",
        "topic": "...",
        "content": "...",
        "insights": "..."
        "message_link": "..."
    }},
    ...
]
Please dont write additional scripts, just write any interesting results.

Then, after this, read all the messages from the file and summarize them into a single document 
{out_path}/summary_<date>.md, try to summarize the most important insights and workflows people
use to code faster, more efficient around certain topics.
Start by summarizing the top 3 findings in 1 or 2 sentences each. 
Include a link to the message(s) that are relevant for the finding, keep this document short, add nothing else.
"""

allowed_tools = ",".join(["Write", "mcp__discord-mcp__search_messages"])
# Build the command
cmd = ["claude", prompt, "--allowedTools", allowed_tools, "--print"]

try:
    result = subprocess.run(
        cmd, capture_output=True, text=True, check=True, timeout=300
    )
except subprocess.TimeoutExpired:
    print("The process did not finish within 5 minutes.")
    exit(1)
except Exception as e:
    print(f"Error: {e.stderr}\n{e.stdout}")
    exit(1)

print(result.stdout, "\n", result.stderr)
