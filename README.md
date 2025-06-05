

# Install
## Screenpipe with deepgram
Download screenpipe from [here](https://web.crabnebula.cloud/mediar/screenpipe/releases), and run it. Make sure to give it access to your microphone and screen. It will store the data in `~/.screenpipe`, in there, there will be a `/data` folder with the raw screenshots and audio recordings. There will also be a sqlite file with transcriptions and ocr results. This is under `~/.screenpipe/db.sqlite`. When you run the app, under settings you can use a better transcriber, we recommend deepgram. You can make a free account [here](https://console.deepgram.com/signup) and paste the key in the app settings tab. You can try transcriptions by just talking to yourself for a minute, acting as if you are in a meeting.

## MCP servers
now we can set up our MCP servers for Claude Desktop. First we can [create a new github personal access token](https://github.com/settings/personal-access-tokens/new), which we use for our github mcp server
```
export GITHUB_PERSONAL_ACCESS_TOKEN=<my_acces_token>
python scripts/add_mcps_claude_desktop_config.py
````

# Run
Lastly we run our mcp server:
```
pip install -e .
python agentic_syftbox/server.py
```


# Run docker
```
docker build -t mcp-server -f mcp_server.dockerfile .
docker run -p 8000:8000 -v ./data:/app/data -e ANTHROPIC_API_KEY $ANTROPIC_API_KEY mcp-server
```

