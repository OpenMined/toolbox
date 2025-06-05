# Install

```
export GITHUB_PERSONAL_ACCESS_TOKEN=<my_acces_token>
python scripts/add_mcps_claude_desktop_config.py
````

# Run
```
pip install -e .
python agentic_syftbox/server.py
```


# Run docker
```
docker build -t mcp-server -f mcp_server.dockerfile .
docker run -p 8000:8000 -v ./data:/app/data -e ANTHROPIC_API_KEY $ANTROPIC_API_KEY mcp-server
```

